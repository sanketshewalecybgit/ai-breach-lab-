def authorize(db, user, name, args, source='user', approved=False):
    return {'allowed': True, 'authorization': 'NOT CHECKED',
            'reason': 'Intentionally vulnerable: authenticated identity is not bound to tool parameters.'}
