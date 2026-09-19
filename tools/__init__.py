import re
from .profile_tools import get_profile, search_customer
from .order_tools import get_order, lookup_shipping_status
from .support_tools import get_internal_note, read_ticket, create_support_ticket
from .refund_tools import issue_refund
from security import secure_policy, vulnerable_policy

SCHEMAS = {
    'get_profile': {'user_id': int}, 'get_order': {'order_id': str},
    'search_customer': {'email': str}, 'get_internal_note': {'order_id': str},
    'create_support_ticket': {'subject': str, 'message': str},
    'issue_refund': {'order_id': str, 'amount': int}, 'read_ticket': {'ticket_id': int},
    'lookup_shipping_status': {'order_id': str},
}


def validate(name, args):
    if name not in SCHEMAS or not isinstance(args, dict) or set(args) != set(SCHEMAS[name]):
        return 'Unknown tool or invalid argument schema.'
    for key, kind in SCHEMAS[name].items():
        if type(args[key]) is not kind:
            return f'{key} must be {kind.__name__}.'
        if kind is int and key != 'amount' and not 0 < args[key] <= 2**31 - 1:
            return f'{key} is outside the fictional identifier range.'
        if kind is str and (not args[key].strip() or len(args[key]) > 4000):
            return f'{key} is empty or too long.'
    if 'order_id' in args and not re.fullmatch(r'ORD-\d{4}', args['order_id']):
        return 'Use a fictional ORD-#### identifier.'
    if 'email' in args and not re.fullmatch(r'[\w.+-]+@novacart\.lab', args['email'], re.I):
        return 'Only fictional @novacart.lab identities are supported.'
    if 'amount' in args and abs(args['amount']) > 10**9:
        return 'Simulation numeric limit exceeded.'
    return None


def execute(db, user, mode, name, args, source='user', approved=False):
    error = validate(name, args)
    if error:
        return {'error': error, 'status': 400}, 'SCHEMA REJECTED'
    policy = secure_policy if mode == 'secure' else vulnerable_policy
    decision = policy.authorize(db, user, name, args, source, approved)
    if not decision['allowed']:
        result = {'error': decision['reason'], 'status': decision['status']}
        if decision.get('requires_approval'):
            cursor = db.execute('INSERT INTO approvals (requested_by, order_id, amount) VALUES (?, ?, ?)',
                                (user['id'], args['order_id'], args['amount']))
            result.update(requires_approval=True, approval_id=cursor.lastrowid)
        return result, decision['authorization']
    if name == 'issue_refund':
        result = issue_refund(db, **args, authenticated_user=user['id'])
    elif name == 'create_support_ticket':
        result = create_support_ticket(db, **args, authenticated_user=user['id'])
    elif name == 'get_internal_note':
        result = get_internal_note(db, **args, secure=mode == 'secure')
    else:
        result = {'get_profile': get_profile, 'get_order': get_order, 'search_customer': search_customer,
                  'read_ticket': read_ticket, 'lookup_shipping_status': lookup_shipping_status}[name](db, **args)
    return result, decision['authorization']
