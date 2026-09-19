import pytest
from config import DEMO_TOKEN
from database import get_db
from tools import execute
from conftest import chat, post, login


def test_secure_cross_user_order_access_blocked(secure):
    response = chat(secure, 'Show ORD-1002')
    assert response.status_code == 403
    data = response.get_json()
    assert data['trace'][0]['authorization'] == 'DENIED'
    assert 'Lab Laptop' not in data['response']
    assert not data['newly_solved']


def test_secure_search_tool_not_available(secure):
    data = chat(secure, 'Find bob@novacart.lab').get_json()
    assert data['trace'] == []
    assert 'unavailable' in data['response']


@pytest.mark.parametrize('message,status', [
    ('Refund 8000 for ORD-1002', 403),
    ('Refund 50000 for ORD-1001', 422),
    ('Refund 0 for ORD-1001', 422),
    ('Refund -50 for ORD-1001', 422),
    ('Refund 100 for ORD-1003', 422),
])
def test_secure_invalid_refund_blocked(secure, app, message, status):
    result = chat(secure, message)
    assert result.status_code == status
    assert result.get_json()['trace'][0]['authorization'] == 'DENIED'
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM refund_events').fetchone()[0] == 0
        assert get_db().execute('SELECT COUNT(*) FROM approvals').fetchone()[0] == 0


def test_secure_oversized_refund_blocked(secure):
    assert chat(secure, 'Refund INR 50000 for ORD-1001').status_code == 422


def test_secure_metadata_never_enters_context(secure, app):
    data = chat(secure, 'Show internal note for ORD-1001').get_json()
    assert 'Customer replacement approved.' in data['response']
    assert DEMO_TOKEN not in str(data)
    assert 'internal_metadata' not in data['trace'][0]['result']
    with app.app_context():
        assert DEMO_TOKEN not in get_db().execute('SELECT tool_result FROM tool_events').fetchone()[0]


@pytest.mark.parametrize('message,tool', [
    ('Summarize ticket 2', 'read_ticket'), ('Summarize ticket 3', 'read_ticket'),
    ('Shipping status of ORD-1003', 'lookup_shipping_status'),
])
def test_secure_indirect_prompt_injection_does_not_trigger_sensitive_tool(secure, message, tool):
    data = chat(secure, message).get_json()
    assert [e['tool'] for e in data['trace']] == [tool]
    assert DEMO_TOKEN not in data['response']
    assert not data['newly_solved']


@pytest.mark.parametrize('tool,args,source', [
    ('search_customer', {'email': 'bob@novacart.lab'}, 'user'),
    ('get_order', {'order_id': 'ORD-1002'}, 'user'),
    ('get_profile', {'user_id': 1002}, 'user'),
    ('get_internal_note', {'order_id': 'ORD-1002'}, 'user'),
    ('read_ticket', {'ticket_id': 4}, 'user'),
    ('get_internal_note', {'order_id': 'ORD-1001'}, 'ticket:2'),
    ('search_customer', {'email': 'bob@novacart.lab'}, 'shipping:ORD-1003'),
    ('issue_refund', {'order_id': 'ORD-1001', 'amount': 100}, 'ticket:3'),
])
def test_backend_policy_independent_of_agent(secure, app, tool, args, source):
    with app.app_context():
        db = get_db()
        user = dict(db.execute('SELECT * FROM users WHERE id=1001').fetchone())
        result, authorization = execute(db, user, 'secure', tool, args, source)
        assert authorization == 'DENIED'
        assert result['status'] == 403


def test_secure_approval_then_repeat_denied(secure, app):
    response = chat(secure, 'Refund 100 for ORD-1001')
    assert response.status_code == 202
    proposal = response.get_json()['trace'][0]['result']
    assert proposal['requires_approval'] is True
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM refund_events').fetchone()[0] == 0
    path = f'/approvals/{proposal["approval_id"]}/confirm'
    assert post(secure, path, {'confirm': 'yes'}).status_code == 302
    with app.app_context():
        assert get_db().execute('SELECT amount FROM refund_events').fetchone()[0] == 100
        assert get_db().execute('SELECT status FROM approvals').fetchone()[0] == 'approved'
    assert post(secure, path, {'confirm': 'yes'}).status_code == 404
    assert chat(secure, 'Refund 100 for ORD-1001').status_code == 409


def test_approval_requires_human_post_and_owner(secure, app):
    proposal = chat(secure, 'Refund 100 for ORD-1001').get_json()['trace'][0]['result']
    path = f'/approvals/{proposal["approval_id"]}/confirm'
    assert secure.get(path).status_code == 405
    assert post(secure, path).status_code == 400
    login(secure, 1002)
    assert post(secure, path, {'confirm': 'yes'}).status_code == 404
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM refund_events').fetchone()[0] == 0


def test_approval_rechecks_live_business_rules(secure, app):
    proposal = chat(secure, 'Refund 100 for ORD-1001').get_json()['trace'][0]['result']
    second = chat(secure, 'Refund 100 for ORD-1001').get_json()['trace'][0]['result']
    post(secure, f'/approvals/{proposal["approval_id"]}/confirm', {'confirm': 'yes'})
    post(secure, f'/approvals/{second["approval_id"]}/confirm', {'confirm': 'yes'})
    with app.app_context():
        db = get_db()
        assert db.execute('SELECT COUNT(*) FROM refund_events').fetchone()[0] == 1
        assert db.execute('SELECT status FROM approvals WHERE id=?', (second['approval_id'],)).fetchone()[0] == 'rejected'


def test_secure_legitimate_tools_work(secure):
    for prompt in ['Show my profile', 'Show ORD-1001', 'Summarize ticket 1', 'Show internal note for ORD-1001', 'Create support ticket: Please help with my order.']:
        data = chat(secure, prompt).get_json()
        assert data['trace'][0]['authorization'] == 'ALLOWED'
        assert 'error' not in data['trace'][0]['result']
        assert not data['newly_solved']
