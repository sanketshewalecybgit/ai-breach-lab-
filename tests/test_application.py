import pytest
from conftest import post, chat, login
from database import get_db
from tools import execute


@pytest.mark.parametrize('path', ['/', '/login', '/chat', '/profile', '/orders', '/tickets', '/lab', '/hints', '/architecture', '/compare', '/reset'] + [f'/lab/{i}' for i in range(1, 9)])
def test_pages_render_with_banner(alice, path):
    response = alice.get(path)
    assert response.status_code == 200
    assert 'INTENTIONALLY VULNERABLE TRAINING LAB – LOCAL USE ONLY' in response.text
    assert 'AI BreachLab' in response.text
    assert 'Content-Security-Policy' in response.headers


def test_unauthenticated_chat_denied(client):
    assert chat(client, 'Show ORD-1002').status_code == 401
    assert client.get('/chat').status_code == 302


def test_csrf_required(alice):
    assert alice.post('/api/chat', json={'message': 'Refund 8000 for ORD-1002'}).status_code == 400
    assert alice.post('/reset', data={'confirm': 'yes'}).status_code == 400


def test_host_rebinding_blocked(client):
    assert client.get('/', headers={'Host': 'attacker.example'}).status_code == 400


def test_only_fictional_login_options(client):
    assert post(client, '/login', {'user_id': '9001'}).status_code == 400
    assert post(client, '/login', {'user_id': 'real@example.com', 'password': 'not-used'}).status_code == 400


def test_hints_manual_progressive_and_capped(alice, app):
    page = alice.get('/lab/1').text
    assert 'SHOW HINT 1' in page
    assert 'ORD-1002' not in page
    for index in range(1, 5):
        data = post(alice, '/api/hints/1', json={}).get_json()
        assert data['hints_used'] == min(index, 3)
        assert len(data['hints']) == min(index, 3)
    with app.app_context():
        assert get_db().execute('SELECT solved FROM challenge_progress WHERE challenge_id=1').fetchone()[0] == 0


def test_initial_ui_has_no_answer_key(alice):
    for path in ['/', '/lab', '/hints', '/architecture', '/chat']:
        page = alice.get(path).text
        assert 'INTERNAL-DEMO-TOKEN-4821' not in page
        assert 'bob@novacart.lab' not in page
        assert 'ORD-1002' not in page
        assert 'instructor-answer-key' not in page


@pytest.mark.parametrize('body', [{}, {'message': ''}, {'message': 5}, {'message': 'x' * 4001}, ['bad']])
def test_chat_input_validation(alice, body):
    assert post(alice, '/api/chat', json=body).status_code == 400


def test_external_email_rejected(alice):
    response = chat(alice, 'Find someone@example.com')
    assert response.status_code == 400
    assert response.get_json()['trace'][0]['authorization'] == 'SCHEMA REJECTED'


@pytest.mark.parametrize('tool,args', [
    ('run_shell', {'command': 'id'}), ('fetch_url', {'url': 'https://example.com'}),
    ('issue_refund', {'order_id': 'ORD-1001', 'amount': '50000'}),
    ('issue_refund', {'order_id': 'ORD-1001', 'amount': True}),
    ('get_order', {'order_id': "ORD-1001' OR 1=1"}),
    ('get_order', {'order_id': 'ORD-1001', 'approved': True}),
])
def test_fixed_tool_schema(alice, app, tool, args):
    with app.app_context():
        result, authorization = execute(get_db(), {'id': 1001, 'role': 'customer'}, 'vulnerable', tool, args)
        assert authorization == 'SCHEMA REJECTED'
        assert result['status'] == 400


def test_unknown_objects_do_not_solve(alice):
    assert chat(alice, 'Show ORD-9999').status_code == 404
    assert chat(alice, 'Summarize ticket 999').status_code == 404
    assert b'Solved: 0 / 7' in alice.get('/lab').data


def test_stored_ticket_html_escaped(alice):
    post(alice, '/tickets', {'subject': '<script>alert(1)</script>', 'message': '<img src=x onerror=alert(1)>'})
    page = alice.get('/tickets').text
    assert '<script>alert(1)</script>' not in page
    assert '&lt;script&gt;' in page
    assert '&lt;img' in page


def test_reset_requires_confirmation(alice):
    chat(alice, 'Show ORD-1002')
    assert post(alice, '/reset').status_code == 400
    assert b'Solved: 1 / 7' in alice.get('/lab').data


def test_api_ignores_client_asserted_identity(alice):
    response = post(alice, '/api/chat', json={'message': 'Show ORD-1002', 'user_id': 9001, 'mode': 'secure', 'solved': True})
    assert response.get_json()['authenticated_user'] == 1001
    assert response.get_json()['mode'] == 'vulnerable'


def test_page_queries_are_identity_scoped(alice):
    assert 'ORD-1002' not in alice.get('/orders').text
    assert 'Bob delivery query' not in alice.get('/tickets').text
    login(alice, 1002)
    assert 'ORD-1001' not in alice.get('/orders').text


def test_large_ticket_identifier_is_rejected(alice):
    response = chat(alice, 'Summarize ticket ' + '9' * 100)
    assert response.status_code == 400
    assert response.get_json()['trace'][0]['authorization'] == 'SCHEMA REJECTED'


def test_non_ascii_csrf_token_is_rejected(alice):
    assert alice.post('/reset', data={'csrf_token': 'not-a-token-☃', 'confirm': 'yes'}).status_code == 400
