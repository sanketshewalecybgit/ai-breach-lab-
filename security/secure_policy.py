CUSTOMER_TOOLS = {'get_profile', 'get_order', 'get_internal_note', 'read_ticket',
                  'create_support_ticket', 'issue_refund', 'lookup_shipping_status'}


def deny(reason, status=403):
    return {'allowed': False, 'authorization': 'DENIED', 'reason': reason, 'status': status}


def authorize(db, user, name, args, source='user', approved=False):
    if source != 'user':
        return deny('Risk policy: untrusted retrieved content cannot authorize a tool transition.')
    if user['role'] == 'customer' and name not in CUSTOMER_TOOLS:
        return deny('Tool scope: global customer search is unavailable to customer-facing agents.')
    if name == 'get_profile' and args['user_id'] != user['id']:
        return deny('Object authorization: this profile belongs to another identity.')
    if 'order_id' in args:
        order = db.execute('SELECT * FROM orders WHERE id = ?', (args['order_id'],)).fetchone()
        # Same response for missing and inaccessible objects avoids an existence oracle.
        if not order or order['user_id'] != user['id']:
            return deny('Object authorization: order is unavailable to this identity.')
        if name == 'issue_refund':
            if not 0 < args['amount'] <= order['amount']:
                return deny('Business rule: refund must be positive and no greater than the amount paid.', 422)
            if order['refunded']:
                return deny('Business rule: this order has already been refunded.', 409)
            if order['status'] != 'delivered':
                return deny('Business rule: only delivered orders are eligible for a refund.', 422)
            if not approved:
                return {'allowed': False, 'authorization': 'APPROVAL REQUIRED', 'status': 202,
                        'requires_approval': True, 'reason': 'A human must approve this simulated refund.'}
    if name == 'read_ticket':
        ticket = db.execute('SELECT created_by FROM support_tickets WHERE id = ?', (args['ticket_id'],)).fetchone()
        if not ticket or ticket['created_by'] != user['id']:
            return deny('Object authorization: ticket is unavailable to this identity.')
    return {'allowed': True, 'authorization': 'ALLOWED',
            'reason': 'Independent tool scope, object authorization, business and risk checks passed.'}
