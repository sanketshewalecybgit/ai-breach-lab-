"""Deterministic task parsing, provenance, and grading of actual Expert effects."""
import copy
import json
import re
from datetime import datetime, timezone
from .cases import BY_ID, identifier, save
from .tools import execute


HELP = ('Use one task per message. Supported tasks: Search documents <words>; Read document <ID>; '
        'Prepare support summary; Check delivery <order ID>; Request refund INR <amount> for <order ID>; '
        'Revise proposal <ID> to INR <amount>; Execute proposal <ID>; '
        'Export document <ID> to customer; Remember destination customer. '
        'Find case IDs in the documents, order list, and proposal panel. This is a deterministic simulator.')


def call(tool, args, source=None):
    return dict(tool=tool, arguments=args, source=source or {'kind': 'user'})


def parse(message):
    text = message.strip().rstrip('.').strip()
    patterns = [
        (r'(?:search|find) documents?\s+(.+)', lambda m: call('search_documents', {'query': m[1]})),
        (r'(?:read|summarize|open) document\s+(DOC-[A-F0-9]{8})', lambda m: call('read_document', {'document_id': m[1].upper()})),
        (r'export document\s+(DOC-[A-F0-9]{8})\s+to\s+(customer|review)', lambda m: call('export_document', {'document_id': m[1].upper(), 'destination': m[2].lower()})),
        (r'remember destination\s+(customer|review)', lambda m: call('remember_destination', {'destination': m[1].lower()})),
        (r'prepare (?:my )?support summary', lambda m: call('prepare_summary', {})),
        (r'check delivery\s+(ORD-[A-F0-9]{8})', lambda m: call('get_integration', {})),
        (r'(?:request )?refund(?: INR)?\s+([0-9]{1,10})\s+for\s+(ORD-[A-F0-9]{8})', lambda m: call('request_refund', {'amount': int(m[1]), 'order_id': m[2].upper()})),
        (r'revise proposal\s+(PR-[A-F0-9]{8})\s+to(?: INR)?\s+([0-9]{1,10})', lambda m: call('revise_proposal', {'proposal_id': m[1].upper(), 'amount': int(m[2])})),
        (r'execute proposal\s+(PR-[A-F0-9]{8})', lambda m: call('execute_proposal', {'proposal_id': m[1].upper()})),
    ]
    for pattern, build in patterns:
        match = re.fullmatch(pattern, text, re.I)
        if match:
            proposal = build(match)
            if proposal['tool'] == 'get_integration':
                # User-requested delivery step, distinct from publisher instructions.
                return [proposal, call('delivery_status', {'order_id': match[1].upper()})]
            return [proposal]
    return []


def directives(body, source):
    """Small public grammar for editable fictional reference/metadata content."""
    calls = []
    pattern = r'\[agent:\s*(?:export\s+(DOC-[A-F0-9]{8})\s+to\s+(customer|review)|remember\s+destination=(customer|review))\s*\]'
    for match in re.finditer(pattern, body, re.I):
        if match[1]:
            calls.append(call('export_document', {'document_id': match[1].upper(), 'destination': match[2].lower()}, source))
        else:
            calls.append(call('remember_destination', {'destination': match[3].lower()}, source))
        if len(calls) == 4:
            break
    return calls


def followups(event):
    result = event['result']
    if 'error' in result:
        return []
    if event['tool'] in ('read_document', 'get_integration'):
        kind = 'document' if event['tool'] == 'read_document' else 'integration'
        source = dict(kind=kind, id=result['id'], event_id=event['id'])
        return directives(result['body'] if kind == 'document' else result['description'], source)
    if event['tool'] == 'prepare_summary':
        memory = result['applied_memory']
        source = dict(kind='task', event_id=event['id'])
        if memory and memory['source']['kind'] != 'user':
            source = dict(kind='memory', id=memory['id'], event_id=event['id'],
                          origin_interaction=memory['interaction_id'], origin_event=memory['event_id'],
                          origin_source=copy.deepcopy(memory['source']))
        return [call('export_document', {'document_id': result['document_id'], 'destination': result['destination']}, source)]
    return []


def evaluate(case, mode, interaction_id, events):
    if mode != 'vulnerable':
        return []
    earned = {}
    successful = {e['id']: e for e in events if 'error' not in e['result']}
    for event in successful.values():
        result, source = event['result'], event['source']
        evidence = dict(interaction_id=interaction_id, event_id=event['id'], tool=event['tool'])
        if event['tool'] == 'read_document' and result['tenant'] != case['tenant'] and result['body']:
            earned['tenant'] = dict(evidence, authenticated_tenant=case['tenant'], document_tenant=result['tenant'],
                                    document_id=result['id'], disclosed_content=result['body'])
        if event['tool'] == 'export_document' and result['destination'] == 'review':
            parent = successful.get(source.get('event_id'))
            disclosure = dict(evidence, outbox_id=result['id'], document_id=result['document_id'],
                              destination=result['destination'], source=source)
            if result['classification'] == 'internal' and parent and parent['result'].get('id') == source.get('id'):
                if source['kind'] == 'document' and parent['tool'] == 'read_document':
                    earned['reference'] = disclosure
                if source['kind'] == 'integration' and parent['tool'] == 'get_integration':
                    earned['integration'] = disclosure
            if (source['kind'] == 'memory' and source['origin_interaction'] != interaction_id
                    and source['origin_source']['kind'] == 'document' and parent
                    and parent['tool'] == 'prepare_summary' and result['document_id'] == case['summary_document']):
                earned['memory'] = dict(disclosure, earlier_interaction=source['origin_interaction'],
                                        memory_write_event=source['origin_event'])
        if event['tool'] == 'execute_proposal':
            refund = result['refund']
            approval = refund['approval']
            changed = any(refund[k] != approval[k] for k in ('order_id', 'amount'))
            expired = approval['expires_at'] <= refund['executed_at']
            if changed or expired or approval['used']:
                earned['approval'] = dict(evidence, refund_id=refund['id'], approval_id=approval['id'],
                                          approved_amount=approval['amount'], executed_amount=refund['amount'],
                                          approved_revision=approval['revision'], executed_revision=refund['revision'],
                                          replayed=approval['used'], expired=expired)
    new = []
    for mission, evidence in earned.items():
        if mission not in case['progress']:
            case['progress'][mission] = evidence
            new.append(dict(id=mission, title=BY_ID[mission]['title'], evidence=evidence))
    return new


def record(db, case, payload):
    payload['recorded_at'] = datetime.now(timezone.utc).isoformat()
    db.execute('INSERT INTO expert_interactions (case_id, actor, interaction_id, payload_json) VALUES (?, ?, ?, ?)',
               (case['id'], case['actor'], payload['interaction_id'], json.dumps(payload)))
    save(db, case)


def run(db, case, mode, message):
    interaction_id = identifier('RUN')
    queue = parse(message)
    events = []
    while queue and len(events) < 6:
        proposal = queue.pop(0)
        event_id = identifier('EV')
        result, authorization = execute(case, mode, proposal['tool'], proposal['arguments'],
                                        proposal['source'], interaction_id, event_id)
        event = dict(id=event_id, **proposal, authorization=authorization, result=result)
        events.append(event)
        queue.extend(followups(event))
    earned = evaluate(case, mode, interaction_id, events)
    payload = dict(interaction_id=interaction_id, mode=mode, message=message, trace=events,
                   authenticated_user=case['actor'], tenant=case['tenant'], customer=case['customer'],
                   response='Inspect the executed results below.' if events else HELP,
                   newly_solved=earned, limit_reached=bool(queue))
    record(db, case, payload)
    return payload
