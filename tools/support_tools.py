def get_internal_note(db, order_id, secure=False):
    row = db.execute('SELECT * FROM internal_notes WHERE order_id = ?', (order_id,)).fetchone()
    if not row:
        return {'error': 'Note not found', 'status': 404}
    # Minimize data BEFORE the tool result reaches the agent context.
    result = {'order_id': order_id, 'support_note': row['customer_visible_text']}
    if not secure:
        result['internal_metadata'] = row['internal_metadata']
    return result


def read_ticket(db, ticket_id):
    row = db.execute('SELECT id, created_by, subject, message FROM support_tickets WHERE id = ?', (ticket_id,)).fetchone()
    return dict(row) if row else {'error': 'Ticket not found', 'status': 404}


def create_support_ticket(db, subject, message, authenticated_user):
    cursor = db.execute('INSERT INTO support_tickets (created_by, subject, message) VALUES (?, ?, ?)',
                        (authenticated_user, subject, message))
    return {'status': 'ticket_created', 'ticket_id': cursor.lastrowid, 'subject': subject}
