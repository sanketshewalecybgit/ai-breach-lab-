def get_profile(db, user_id):
    row = db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    return dict(row) if row else {'error': 'User not found', 'status': 404}


def search_customer(db, email):
    row = db.execute('SELECT * FROM users WHERE lower(email) = lower(?)', (email,)).fetchone()
    return dict(row) if row else {'error': 'Customer not found', 'status': 404}
