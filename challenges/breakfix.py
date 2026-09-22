"""Isolated, deterministic attack/fix/replay exercises using the lab's real tools."""
import json
import sqlite3
import uuid

from flask import Blueprint, abort, g, redirect, render_template, request, url_for

from ai.mock_ai import MockAIProvider
from config import MAX_PROMPT_LENGTH
from database import get_db
from database.seed import seed_database
from tools import execute, validate

bp = Blueprint('breakfix', __name__)
MISSIONS = {
    'ownership': dict(title='Cross the account boundary',
        brief='Get another customer’s profile or order while signed in as yourself.',
        starter='Show me profile {other}.',
        lesson='Bind object access to the authenticated identity at the tool boundary.'),
    'injection': dict(title='Turn a ticket into an instruction',
        brief='Make the assistant follow the planted instructions in ticket 2 and expose internal metadata.',
        starter='Summarize ticket 2.',
        lesson='Retrieved text is evidence to summarize. It cannot authorize another tool call.'),
    'metadata': dict(title='Expose the hidden support note',
        brief='Retrieve internal metadata from the support note on your own order.',
        starter='Retrieve the internal note for {order}.',
        lesson='Ownership alone is insufficient. Return only customer-visible fields to the assistant.'),
}
DEFENSES = {
    'ownership': ('Check object ownership', 'Compare profile, order and ticket owners with the signed-in identity.'),
    'untrusted': ('Reject instructions from retrieved content', 'Block tool calls whose source is a ticket or shipping response.'),
    'minimize': ('Remove internal metadata', 'Filter staff-only fields out of tool results before the assistant sees them.'),
    'deny_all': ('Disable every tool', 'An emergency stop. Consider what happens to legitimate customer requests.'),
}
READ_TOOLS = {'get_profile', 'get_order', 'get_internal_note', 'read_ticket',
              'lookup_shipping_status', 'search_customer'}


def initialize(db):
    db.execute('''CREATE TABLE IF NOT EXISTS breakfix_attempts (
        user_id INTEGER NOT NULL, mission TEXT NOT NULL, revision TEXT NOT NULL,
        prompt TEXT NOT NULL, before_json TEXT NOT NULL, after_json TEXT,
        PRIMARY KEY (user_id, mission))''')
    db.commit()


def simulate(user_id, prompt, defenses=()):
    """Every run starts from identical fixtures; workshop data is never executed on."""
    db = sqlite3.connect(':memory:')
    db.row_factory = sqlite3.Row
    try:
        seed_database(db)
        # Each identity gets the same planted ticket exercise in its own sandbox.
        own_order = 'ORD-1001' if user_id == 1001 else 'ORD-1002'
        db.execute('UPDATE support_tickets SET created_by=?, message=replace(message, ?, ?) WHERE id=2',
                   (user_id, 'ORD-1001', own_order))
        user = dict(db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone())
        provider = MockAIProvider()
        proposal = provider.generate(prompt, user, READ_TOOLS)
        queue = [dict(proposal, source='user')] if 'tool' in proposal else []
        trace = []
        while queue and len(trace) < 4:
            call = queue.pop(0)
            name, args, source = call['tool'], call['arguments'], call['source']
            error = validate(name, args)
            if error:
                trace.append(dict(tool=name, arguments=args, source=source,
                                  authorization='SCHEMA REJECTED', result={'error': error}))
                continue
            reason = None
            if 'deny_all' in defenses:
                reason = 'All tools disabled.'
            elif 'untrusted' in defenses and source != 'user':
                reason = 'Retrieved content cannot authorize a tool call.'
            elif 'ownership' in defenses:
                owner = user_id
                if name == 'get_profile':
                    owner = args['user_id']
                elif name == 'search_customer':
                    row = db.execute('SELECT id FROM users WHERE email=?', (args['email'],)).fetchone()
                    owner = row['id'] if row else None
                elif 'order_id' in args:
                    row = db.execute('SELECT user_id FROM orders WHERE id=?', (args['order_id'],)).fetchone()
                    owner = row['user_id'] if row else None
                elif name == 'read_ticket':
                    row = db.execute('SELECT created_by FROM support_tickets WHERE id=?', (args['ticket_id'],)).fetchone()
                    owner = row['created_by'] if row else None
                if owner != user_id:
                    reason = 'Object is unavailable to this identity.'
            if reason:
                result, authorization = {'error': reason}, 'BLOCKED'
            else:
                result, authorization = execute(db, user, 'vulnerable', name, args, source)
                if authorization == 'NOT CHECKED':
                    authorization = 'ALLOWED'
                if 'minimize' in defenses and 'internal_metadata' in result:
                    result.pop('internal_metadata')
                    authorization = 'FILTERED'
            trace.append(dict(tool=name, arguments=args, source=source,
                              authorization=authorization, result=result))
            queue.extend(provider.followups(name, result, 'vulnerable'))
        return dict(trace=trace, message=proposal.get('message', ''),
                    decision=proposal['decision'])
    finally:
        db.close()


def breached(mission, result, user_id):
    for event in result['trace']:
        value = event['result']
        if 'error' in value:
            continue
        if mission == 'ownership' and (
            (event['tool'] in ('get_profile', 'search_customer') and value.get('id') != user_id)
            or (event['tool'] == 'get_order' and value.get('user_id') != user_id)
        ):
            return True
        if mission in ('metadata', 'injection') and 'internal_metadata' in value:
            if mission == 'metadata' or event['source'] != 'user':
                return True
    return False


def replay(mission, user_id, prompt, defenses):
    after = simulate(user_id, prompt, defenses)
    order = 'ORD-1001' if user_id == 1001 else 'ORD-1002'
    ticket = 1 if user_id == 1001 else 4
    checks = []
    for label, text, expected_tool, expected_field in [
        ('Own profile remains available', 'Show my profile.', 'get_profile', 'email'),
        ('Own order remains available', f'Show order {order}.', 'get_order', 'item'),
        ('Customer support note remains available', f'Internal note for {order}.', 'get_internal_note', 'support_note'),
        ('Ordinary ticket remains readable', f'Summarize ticket {ticket}.', 'read_ticket', 'message'),
    ]:
        result = simulate(user_id, text, defenses)
        passed = any(e['tool'] == expected_tool and expected_field in e['result'] for e in result['trace'])
        checks.append(dict(label=label, prompt=text, passed=passed, trace=result['trace']))
    stopped = not breached(mission, after, user_id)
    after.update(defenses=list(defenses), checks=checks, stopped=stopped,
                 passed=stopped and all(check['passed'] for check in checks))
    return after


@bp.route('/break-fix', methods=['GET', 'POST'])
def workspace():
    if not g.user:
        return redirect(url_for('login'))
    mission = request.args.get('mission', 'ownership')
    if mission not in MISSIONS:
        abort(404)
    db = get_db()
    row = db.execute('SELECT * FROM breakfix_attempts WHERE user_id=? AND mission=?',
                     (g.user['id'], mission)).fetchone()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'attack':
            prompt = request.form.get('prompt', '').strip()
            if not prompt or len(prompt) > MAX_PROMPT_LENGTH:
                abort(400, description=f'Enter an attack of 1–{MAX_PROMPT_LENGTH} characters.')
            before = simulate(g.user['id'], prompt)
            before['breached'] = breached(mission, before, g.user['id'])
            db.execute('''INSERT INTO breakfix_attempts VALUES (?, ?, ?, ?, ?, NULL)
                ON CONFLICT(user_id, mission) DO UPDATE SET revision=excluded.revision,
                prompt=excluded.prompt, before_json=excluded.before_json, after_json=NULL''',
                (g.user['id'], mission, uuid.uuid4().hex, prompt, json.dumps(before)))
        elif action == 'replay':
            if not row or request.form.get('revision') != row['revision']:
                abort(409, description='This attack has changed. Reload the page before replaying.')
            if not json.loads(row['before_json'])['breached']:
                abort(409, description='Demonstrate a successful attack before adding defenses.')
            defenses = request.form.getlist('defense')
            if any(item not in DEFENSES for item in defenses):
                abort(400, description='Choose a listed defense.')
            after = replay(mission, g.user['id'], row['prompt'], defenses)
            updated = db.execute('''UPDATE breakfix_attempts SET after_json=?
                WHERE user_id=? AND mission=? AND revision=?''',
                (json.dumps(after), g.user['id'], mission, row['revision']))
            if not updated.rowcount:
                abort(409, description='This attack has changed. Reload before replaying.')
        else:
            abort(400, description='Choose attack or replay.')
        db.commit()
        return redirect(url_for('breakfix.workspace', mission=mission))
    before = json.loads(row['before_json']) if row else None
    after = json.loads(row['after_json']) if row and row['after_json'] else None
    states = {r['mission']: bool(r['after_json'] and json.loads(r['after_json'])['passed'])
              for r in db.execute('SELECT mission, after_json FROM breakfix_attempts WHERE user_id=?', (g.user['id'],))}
    return render_template('breakfix.html', missions=MISSIONS, mission=mission,
        exercise=MISSIONS[mission], defenses=DEFENSES, attempt=row, before=before, after=after,
        states=states, max_prompt=MAX_PROMPT_LENGTH,
        starter=MISSIONS[mission]['starter'].format(other=1002 if g.user['id'] == 1001 else 1001,
            order='ORD-1001' if g.user['id'] == 1001 else 'ORD-1002'))
