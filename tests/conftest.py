import pytest
from app import create_app


@pytest.fixture

def app(tmp_path):
    return create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'test.db'), 'SECRET_KEY': 'fictional-test-signing-key'})


@pytest.fixture

def client(app):
    return app.test_client()


def csrf(client):
    client.get('/')
    with client.session_transaction() as session:
        return session['csrf_token']


def post(client, path, data=None, json=None):
    token = csrf(client)
    if json is not None:
        return client.post(path, json=json, headers={'X-CSRF-Token': token})
    return client.post(path, data={**(data or {}), 'csrf_token': token})


def login(client, user=1001):
    return post(client, '/login', {'user_id': str(user)})


def chat(client, message):
    return post(client, '/api/chat', json={'message': message})


@pytest.fixture

def alice(client):
    login(client)
    return client


@pytest.fixture

def secure(alice):
    post(alice, '/mode', {'mode': 'secure'})
    return alice
