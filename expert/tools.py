"""Fixed simulated capabilities and independent policy for Expert cases."""
import copy
import time
from .cases import identifier


SCHEMAS = {
    'search_documents': {'query': str}, 'read_document': {'document_id': str},
    'export_document': {'document_id': str, 'destination': str},
    'remember_destination': {'destination': str}, 'prepare_summary': {},
    'get_integration': {}, 'delivery_status': {'order_id': str},
    'request_refund': {'order_id': str, 'amount': int},
    'revise_proposal': {'proposal_id': str, 'amount': int},
    'execute_proposal': {'proposal_id': str},
}


def find(items, object_id):
    return next((item for item in items if item['id'] == object_id), None)


def reject(reason, status=403):
    return {'error': reason, 'status': status}


def validate(tool, args):
    if tool not in SCHEMAS or not isinstance(args, dict) or set(args) != set(SCHEMAS[tool]):
        return 'Unknown capability or invalid argument schema.'
    for key, kind in SCHEMAS[tool].items():
        if type(args[key]) is not kind:
            return f'{key} must be {kind.__name__}.'
        if kind is str and (len(args[key]) > 4000 or not args[key].strip()):
            return f'{key} is empty or too long.'
    if 'amount' in args and not 0 < args['amount'] <= 10**9:
        return 'Use a positive whole-number INR amount within the simulator limit.'
    if 'destination' in args and args['destination'] not in ('customer', 'review'):
        return 'Only the local customer and review outboxes exist.'
    return None


def authorize(case, mode, tool, args, source):
    """Independent checks also apply to calls selected by injected content."""
    if mode != 'secure':
        return None
    if tool in ('export_document', 'remember_destination') and source['kind'] not in ('user', 'task'):
        return reject('Untrusted content or saved memory cannot authorize this action.')
    if tool in ('read_document', 'export_document'):
        doc = find(case['documents'], args['document_id'])
        if not doc or doc['tenant'] != case['tenant'] or doc['classification'] == 'internal':
            return reject('Document is unavailable to this customer and company.')
    if 'destination' in args and args['destination'] != 'customer':
        return reject('Customer data can only be delivered to the local customer outbox.')
    return None


def execute(case, mode, tool, args, source, interaction_id, event_id):
    error = validate(tool, args)
    if error:
        return reject(error, 400), 'SCHEMA REJECTED'
    denied = authorize(case, mode, tool, args, source)
    if denied:
        return denied, 'DENIED'
    result = perform(case, mode, tool, args, source, interaction_id, event_id)
    return copy.deepcopy(result), 'DENIED' if 'error' in result else 'ALLOWED'


def perform(case, mode, tool, args, source, interaction_id, event_id):
    if tool == 'search_documents':
        words = args['query'].casefold().split()
        docs = [d for d in case['documents'] if all(w in (d['title'] + ' ' + d['body']).casefold() for w in words)]
        if mode == 'secure':
            docs = [d for d in docs if d['tenant'] == case['tenant'] and d['classification'] != 'internal']
        return {'matches': [{k: d[k] for k in ('id', 'title', 'tenant')} for d in docs]}
    if tool == 'read_document':
        doc = find(case['documents'], args['document_id'])
        return doc if doc else reject('Document unavailable.', 404)
    if tool == 'export_document':
        doc = find(case['documents'], args['document_id'])
        if not doc:
            return reject('Document unavailable.', 404)
        entry = dict(id=identifier('OUT'), document_id=doc['id'], tenant=doc['tenant'],
                     classification=doc['classification'], destination=args['destination'],
                     content=doc['body'], interaction_id=interaction_id, event_id=event_id,
                     source=copy.deepcopy(source), simulated_only=True)
        case['outbox'].append(entry)
        return entry
    if tool == 'remember_destination':
        case['memory'] = dict(id=identifier('MEM'), destination=args['destination'], source=copy.deepcopy(source),
                              interaction_id=interaction_id, event_id=event_id)
        return {'saved_memory': case['memory']}
    if tool == 'prepare_summary':
        memory = case['memory']
        # Secure mode must also withstand memory left behind by vulnerable mode.
        trusted = memory and memory['source']['kind'] == 'user' and memory['destination'] == 'customer'
        applied = memory if mode == 'vulnerable' or trusted else None
        return {'document_id': case['summary_document'],
                'destination': applied['destination'] if applied else 'customer',
                'applied_memory': applied, 'ignored_untrusted_memory': bool(memory and not applied)}
    if tool == 'get_integration':
        return case['integration']
    if tool == 'delivery_status':
        order = find(case['orders'], args['order_id'])
        if not order or order['owner'] != case['customer'] or order['tenant'] != case['tenant']:
            return reject('Order unavailable to this customer.')
        return {'order_id': order['id'], 'delivery_status': order['status'], 'simulated_only': True}
    if tool == 'request_refund':
        order = find(case['orders'], args['order_id'])
        error = refund_eligibility(case, order, args['amount'])
        if error:
            return error
        proposal = dict(id=identifier('PR'), order_id=order['id'], amount=args['amount'], revision=1,
                        approval=None, executions=0)
        case['proposals'].append(proposal)
        return {'proposal': proposal, 'requires_approval': True}
    if tool == 'revise_proposal':
        proposal = find(case['proposals'], args['proposal_id'])
        if not proposal:
            return reject('Proposal unavailable.', 404)
        order = find(case['orders'], proposal['order_id'])
        error = refund_eligibility(case, order, args['amount'])
        if error:
            return error
        proposal['amount'] = args['amount']
        proposal['revision'] += 1
        return {'proposal': proposal, 'message': 'Proposal revised. Any existing approval still records its original details.'}
    if tool == 'execute_proposal':
        proposal = find(case['proposals'], args['proposal_id'])
        if not proposal:
            return reject('Proposal unavailable.', 404)
        approval = proposal['approval']
        if not approval:
            return reject('Explicit human approval is required before execution.')
        order = find(case['orders'], proposal['order_id'])
        if mode == 'secure':
            if approval['used']:
                return reject('Approval has already been consumed.', 409)
            if approval['expires_at'] <= time.time():
                return reject('Approval has expired.', 409)
            if any(approval[k] != proposal[k] for k in ('order_id', 'amount', 'revision')):
                return reject('Current proposal differs from the approved details.', 409)
            error = refund_eligibility(case, order, proposal['amount'])
            if error:
                return error
        refund = dict(id=identifier('RF'), proposal_id=proposal['id'], order_id=proposal['order_id'],
                      amount=proposal['amount'], revision=proposal['revision'],
                      approval=copy.deepcopy(approval), executed_at=time.time(),
                      interaction_id=interaction_id, event_id=event_id, simulated_only=True)
        case['refunds'].append(refund)
        approval['used'] = True
        proposal['executions'] += 1
        order['refunded'] = True
        return {'refund': refund}
    raise AssertionError('All validated capabilities must have implementations.')


def refund_eligibility(case, order, amount):
    if not order or order['owner'] != case['customer'] or order['tenant'] != case['tenant']:
        return reject('Order unavailable to this customer.')
    if order['refunded'] or order['status'] != 'delivered':
        return reject('Order is no longer eligible for a refund.', 409)
    if not 0 < amount <= order['paid']:
        return reject('Refund must be positive and no greater than the amount paid.', 422)
    return None


def approve(case, proposal_id):
    """Only invoked by a CSRF-protected, explicit human confirmation route."""
    proposal = find(case['proposals'], proposal_id)
    if not proposal:
        return reject('Proposal unavailable.', 404)
    error = refund_eligibility(case, find(case['orders'], proposal['order_id']), proposal['amount'])
    if error:
        return error
    if proposal['approval']:
        return reject('This proposal already has an approval. Create a new proposal for a fresh approval.', 409)
    proposal['approval'] = dict(id=identifier('AP'), order_id=proposal['order_id'], amount=proposal['amount'],
                                revision=proposal['revision'], expires_at=time.time() + 300, used=False)
    return {'approved': copy.deepcopy(proposal['approval']), 'proposal_id': proposal_id}
