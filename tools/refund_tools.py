from .order_tools import get_order


def issue_refund(db, order_id, amount, authenticated_user):
    order = get_order(db, order_id)
    if 'error' in order:
        return order
    # Intentionally no business policy here: dispatcher selects vulnerable/secure policy.
    cursor = db.execute(
        'INSERT INTO refund_events (order_id, requested_by, amount) VALUES (?, ?, ?)',
        (order_id, authenticated_user, amount))
    db.execute('UPDATE orders SET refunded = 1 WHERE id = ?', (order_id,))
    return {'status': 'refund_simulated', 'event_id': cursor.lastrowid, 'order_id': order_id,
            'owner': order['user_id'], 'amount': amount, 'paid_amount': order['amount'], 'currency': 'INR',
            'simulated_only': True}
