import argparse
import hmac
import json
import secrets
from functools import wraps
from pathlib import Path
from flask import Flask, abort, flash, g, jsonify, redirect, render_template, request, session, url_for
from werkzeug.exceptions import SecurityError
from config import DATABASE, MAX_PROMPT_LENGTH
from database import get_db, close_db
from database.seed import seed_database
from ai.agent import SupportAgent
from challenges.definitions import CHALLENGES, BY_ID, LEVELS
from tools import execute
from expert import cases as expert_cases
from expert.routes import bp as expert_blueprint
from challenges import breakfix


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(SECRET_KEY=secrets.token_hex(32), DATABASE=str(DATABASE),
                      MAX_CONTENT_LENGTH=16384, SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE='Strict', TRUSTED_HOSTS=['127.0.0.1', 'localhost', '[::1]'])
    if test_config:
        app.config.update(test_config)
    app.teardown_appcontext(close_db)
    Path(app.config['DATABASE']).parent.mkdir(parents=True, exist_ok=True)
    with app.app_context():
        db = get_db()
        if not db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").fetchone():
            seed_database(db)
        expert_cases.initialize(db)
        breakfix.initialize(db)
    app.register_blueprint(expert_blueprint)
    app.register_blueprint(breakfix.bp)

    @app.before_request
    def local_request_context():
        if isinstance(request.routing_exception, SecurityError):
            raise request.routing_exception
        session.setdefault('csrf_token', secrets.token_urlsafe(32))
        if request.method == 'POST':
            supplied = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token', '')
            if not hmac.compare_digest(supplied.encode('utf-8'), session['csrf_token'].encode('utf-8')):
                abort(400, description='Missing or invalid CSRF token. Reload this page and try again.')
        row = get_db().execute('SELECT * FROM users WHERE id = ?', (session.get('user_id'),)).fetchone()
        g.user = dict(row) if row else None
        g.mode = get_db().execute('SELECT mode FROM lab_settings WHERE id = 1').fetchone()['mode']

    @app.after_request
    def local_headers(response):
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'none'"
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Cache-Control'] = 'no-store'
        return response

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not g.user:
                if request.path.startswith('/api/'):
                    return jsonify(error='Select a demo identity first.'), 401
                return redirect(url_for('login'))
            return view(*args, **kwargs)
        return wrapped

    def progress():
        rows = get_db().execute('SELECT * FROM challenge_progress ORDER BY challenge_id').fetchall()
        return {row['challenge_id']: dict(row, evidence=json.loads(row['evidence_json'] or '{}')) for row in rows}

    @app.context_processor
    def shared_context():
        states = progress()
        level_progress = {}
        for key in LEVELS:
            members = [c for c in CHALLENGES if c['difficulty'] == key]
            level_progress[key] = dict(
                total=len(members),
                solved=sum(states[c['id']]['solved'] for c in members),
                optional=sum(bool(c.get('optional')) for c in members),
            )
        return dict(identity=g.user, mode=g.mode, csrf_token=session['csrf_token'],
                    challenges=CHALLENGES, progress=states,
                    levels=LEVELS, level_progress=level_progress,
                    solved_count=sum(states[c]['solved'] for c in range(1, 8)))

    @app.get('/')
    def home():
        return render_template('home.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            user_id = request.form.get('user_id')
            if user_id not in ('1001', '1002'):
                abort(400, description='Select Alice or Bob. No passwords or real credentials are accepted.')
            session['user_id'] = int(user_id)
            session['csrf_token'] = secrets.token_urlsafe(32)
            return redirect(url_for('chat'))
        return render_template('login.html')

    @app.post('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    @app.get('/chat')
    @login_required
    def chat():
        approvals = get_db().execute("SELECT * FROM approvals WHERE requested_by = ? AND status = 'pending'", (g.user['id'],)).fetchall()
        return render_template('chat.html', approvals=approvals)

    @app.post('/api/chat')
    @login_required
    def api_chat():
        data = request.get_json(silent=True)
        prompt = data.get('message') if isinstance(data, dict) else None
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > MAX_PROMPT_LENGTH:
            return jsonify(error=f'Provide a message between 1 and {MAX_PROMPT_LENGTH} characters.'), 400
        db = get_db()
        db.execute('BEGIN IMMEDIATE')
        # Read mode inside the write transaction so concurrent toggles cannot mix policies.
        mode = db.execute('SELECT mode FROM lab_settings WHERE id=1').fetchone()['mode']
        result = SupportAgent().run(db, g.user, prompt.strip(), mode)
        status = 200
        if result['trace'] and all('error' in e['result'] for e in result['trace']):
            status = result['trace'][0]['result'].get('status', 400)
        return jsonify(result), status

    @app.post('/approvals/<int:approval_id>/confirm')
    @login_required
    def approve(approval_id):
        db = get_db()
        db.execute('BEGIN IMMEDIATE')
        current_mode = db.execute('SELECT mode FROM lab_settings WHERE id=1').fetchone()['mode']
        if current_mode != 'secure' or request.form.get('confirm') != 'yes':
            abort(400, description='Explicit human confirmation in secure mode is required.')
        row = db.execute("SELECT * FROM approvals WHERE id=? AND requested_by=? AND status='pending'", (approval_id, g.user['id'])).fetchone()
        if not row:
            abort(404)
        args = {'order_id': row['order_id'], 'amount': row['amount']}
        # Revalidate live ownership and business rules, under the same transaction as execution.
        result, authorization = execute(db, g.user, 'secure', 'issue_refund', args, approved=True)
        db.execute('UPDATE approvals SET status=? WHERE id=?', ('rejected' if 'error' in result else 'approved', approval_id))
        db.execute('INSERT INTO tool_events (interaction_id, session_user, user_prompt, mode, source, tool_name, arguments_json, authorization_result, tool_result) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                   (f'approval-{approval_id}', g.user['id'], 'Explicit human confirmation', 'secure', 'human_approval', 'issue_refund', json.dumps(args), authorization, json.dumps(result)))
        db.commit()
        flash(result.get('error', 'Approved: fictional refund simulated. No money was moved.'), 'warning' if 'error' in result else 'success')
        return redirect(url_for('chat'))

    @app.get('/profile')
    @login_required
    def profile():
        return render_template('profile.html')

    @app.get('/orders')
    @login_required
    def orders():
        rows = get_db().execute('SELECT * FROM orders WHERE user_id = ?', (g.user['id'],)).fetchall()
        refunds = get_db().execute('SELECT * FROM refund_events WHERE requested_by = ? ORDER BY id DESC', (g.user['id'],)).fetchall()
        return render_template('orders.html', orders=rows, refunds=refunds)

    @app.route('/tickets', methods=['GET', 'POST'])
    @login_required
    def tickets():
        db = get_db()
        if request.method == 'POST':
            subject, message = request.form.get('subject', '').strip(), request.form.get('message', '').strip()
            if not subject or len(subject) > 120 or not message or len(message) > 4000:
                abort(400, description='A subject (1–120 characters) and message (1–4000 characters) are required.')
            result, _ = execute(db, g.user, g.mode, 'create_support_ticket', {'subject': subject, 'message': message})
            db.commit()
            flash(f'Ticket {result["ticket_id"]} created. Ask the assistant to summarize it.', 'success')
            return redirect(url_for('tickets'))
        rows = db.execute('SELECT * FROM support_tickets WHERE created_by = ? ORDER BY id', (g.user['id'],)).fetchall()
        return render_template('tickets.html', tickets=rows)

    @app.get('/lab')
    def lab():
        selected_level = request.args.get('level', 'all')
        if selected_level == 'expert':
            return redirect(url_for('expert.workspace'))
        if selected_level != 'all' and selected_level not in LEVELS:
            abort(400, description='Choose Beginner, Intermediate, Advanced, or All levels.')
        visible_challenges = [c for c in CHALLENGES
                              if selected_level == 'all' or c['difficulty'] == selected_level]
        return render_template('lab.html', selected_level=selected_level,
                               visible_challenges=visible_challenges)

    @app.get('/lab/<int:challenge_id>')
    def challenge(challenge_id):
        if challenge_id not in BY_ID:
            abort(404)
        return render_template('challenge.html', challenge=BY_ID[challenge_id])

    @app.get('/hints')
    def hints():
        return render_template('hints.html')

    @app.post('/api/hints/<int:challenge_id>')
    @login_required
    def reveal_hint(challenge_id):
        if challenge_id not in BY_ID:
            abort(404)
        db = get_db()
        db.execute('BEGIN IMMEDIATE')
        db.execute('UPDATE challenge_progress SET hints_used = MIN(hints_used + 1, 3) WHERE challenge_id = ?', (challenge_id,))
        count = db.execute('SELECT hints_used FROM challenge_progress WHERE challenge_id = ?', (challenge_id,)).fetchone()[0]
        db.commit()
        return jsonify(hints=BY_ID[challenge_id]['hints'][:count], hints_used=count)

    @app.get('/architecture')
    def architecture():
        return render_template('architecture.html')

    @app.get('/compare')
    def compare():
        return render_template('compare.html')

    @app.post('/mode')
    @login_required
    def set_mode():
        mode = request.form.get('mode')
        if mode not in ('secure', 'vulnerable'):
            abort(400)
        db = get_db()
        db.execute('UPDATE lab_settings SET mode=? WHERE id=1', (mode,))
        db.commit()
        flash(f'{mode.capitalize()} mode enabled. Retest requests in the assistant.', 'success')
        if request.form.get('return_to') == 'expert':
            return redirect(url_for('expert.workspace'))
        return redirect(url_for('chat'))

    @app.get('/solved')
    def solved():
        if not all(progress()[i]['solved'] for i in range(1, 8)):
            return redirect(url_for('lab'))
        return render_template('solved.html')

    @app.route('/reset', methods=['GET', 'POST'])
    def reset():
        if request.method == 'POST':
            if request.form.get('confirm') != 'yes':
                abort(400, description='Reset confirmation is required.')
            seed_database(get_db())
            db = get_db()
            db.execute('BEGIN IMMEDIATE')
            expert_cases.reset(db)
            db.execute('DELETE FROM breakfix_attempts')
            db.commit()
            session.clear()
            flash('Lab reset. Fictional data and original tickets restored; vulnerable mode enabled.', 'success')
            return redirect(url_for('login'))
        return render_template('reset.html')

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(409)
    @app.errorhandler(413)
    @app.errorhandler(422)
    def friendly_error(error):
        if request.path.startswith('/api/'):
            return jsonify(error=error.description), error.code
        # Host validation can fail before the before_request context is available.
        if isinstance(error, SecurityError) or not hasattr(g, 'mode'):
            return 'Local lab request rejected.', error.code
        return render_template('error.html', error=error), error.code

    return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AI BreachLab — hands-on AI security training')
    parser.add_argument('--container', action='store_true', help='Bind inside Docker; publish ONLY to host 127.0.0.1.')
    args = parser.parse_args()
    create_app().run(host='0.0.0.0' if args.container else '127.0.0.1', port=5000, debug=False)
