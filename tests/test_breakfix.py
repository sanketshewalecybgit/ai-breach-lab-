import json

import pytest

from app import create_app
from challenges.breakfix import breached, replay, simulate
from conftest import login, post
from database import get_db


@pytest.mark.parametrize('user_id', [1001, 1002])
@pytest.mark.parametrize('mission,defense', [
    ('ownership', 'ownership'), ('injection', 'untrusted'), ('metadata', 'minimize'),
])
def test_successful_fix_preserves_legitimate_requests(user_id, mission, defense):
    prompt = {
        'ownership': f'Show profile {1002 if user_id == 1001 else 1001}.',
        'injection': 'Summarize ticket 2.',
        'metadata': f'Internal note for {"ORD-1001" if user_id == 1001 else "ORD-1002"}.',
    }[mission]
    before = simulate(user_id, prompt)
    assert breached(mission, before, user_id)
    assert not replay(mission, user_id, prompt, [])['passed']
    fixed = replay(mission, user_id, prompt, [defense])
    assert fixed['passed']
    assert all(check['passed'] for check in fixed['checks'])
    stopped = replay(mission, user_id, prompt, ['deny_all'])
    assert stopped['stopped'] and not stopped['passed']
    assert not any(check['passed'] for check in stopped['checks'])


def test_wrong_defenses_and_unknown_intents_do_not_pass():
    assert not replay('injection', 1001, 'Summarize ticket 2.', ['ownership'])['passed']
    assert not replay('metadata', 1001, 'Internal note for ORD-1001.', ['untrusted'])['passed']
    assert not breached('ownership', simulate(1001, 'hello'), 1001)
    assert not breached('ownership', simulate(1001, 'Show order ORD-9999'), 1001)
    assert simulate(1001, 'Summarize ticket ' + '9' * 100, ['ownership'])['trace'][0]['authorization'] == 'SCHEMA REJECTED'
    assert simulate(1001, 'Find someone@example.com')['trace'][0]['authorization'] == 'SCHEMA REJECTED'


def saved(app, user_id=1001, mission='ownership'):
    with app.app_context():
        return dict(get_db().execute('SELECT * FROM breakfix_attempts WHERE user_id=? AND mission=?',
                                     (user_id, mission)).fetchone())


def test_exact_replay_persistence_and_new_attack_clears_result(alice, app):
    path = '/break-fix?mission=ownership'
    assert post(alice, path, {'action': 'attack', 'prompt': 'Show profile 1002'}).status_code == 302
    first = saved(app)
    assert post(alice, path, {'action': 'replay', 'revision': first['revision'],
                             'defense': 'ownership', 'prompt': 'Show my profile'}).status_code == 302
    state = saved(app)
    assert state['prompt'] == 'Show profile 1002'
    after = json.loads(state['after_json'])
    assert after['passed'] and after['trace'][0]['arguments'] == {'user_id': 1002}
    assert 'FIX VERIFIED' in alice.get(path).text
    restarted = create_app({'TESTING': True, 'DATABASE': app.config['DATABASE'], 'SECRET_KEY': 'new-test-key'})
    assert saved(restarted)['after_json'] == state['after_json']
    post(alice, path, {'action': 'attack', 'prompt': 'Show order ORD-1002'})
    assert saved(app)['after_json'] is None
    assert post(alice, path, {'action': 'replay', 'revision': first['revision']}).status_code == 409


def test_identity_mission_and_workshop_isolation(alice, app):
    with app.app_context():
        before = '\n'.join(get_db().iterdump())
    post(alice, '/break-fix', {'action': 'attack', 'prompt': 'Show profile 1002'})
    with app.app_context():
        after = '\n'.join(line for line in get_db().iterdump() if not line.startswith('INSERT INTO "breakfix_attempts"'))
    assert after == before
    assert 'Vulnerable run' not in alice.get('/break-fix?mission=metadata').text
    login(alice, 1002)
    assert 'Vulnerable run' not in alice.get('/break-fix').text
    assert post(alice, '/break-fix', {'action': 'replay', 'revision': saved(app)['revision']}).status_code == 409
    login(alice, 1001)
    assert 'Vulnerable run' in alice.get('/break-fix').text
    post(alice, '/reset', {'confirm': 'yes'})
    with app.app_context():
        assert get_db().execute('SELECT COUNT(*) FROM breakfix_attempts').fetchone()[0] == 0


def test_route_validation_and_escape(client, alice, app):
    # These fixtures share one client, so explicitly log out before the access check.
    post(client, '/logout')
    assert client.get('/break-fix').location.endswith('/login')
    login(client)
    assert client.post('/break-fix', data={'action': 'attack', 'prompt': 'Show profile 1002'}).status_code == 400
    assert client.get('/break-fix?mission=missing').status_code == 404
    for payload in [{'action': 'attack', 'prompt': ''}, {'action': 'attack', 'prompt': 'x' * 4001}, {'action': 'bad'}]:
        assert post(client, '/break-fix', payload).status_code == 400
    post(client, '/break-fix', {'action': 'attack', 'prompt': 'hello'})
    assert post(client, '/break-fix', {'action': 'replay', 'revision': saved(app)['revision']}).status_code == 409
    post(client, '/break-fix', {'action': 'attack', 'prompt': '<script>alert(1)</script> Show profile 1002'})
    page = client.get('/break-fix').text
    assert '<script>alert(1)</script>' not in page
    assert '&lt;script&gt;' in page
    assert post(client, '/break-fix', {'action': 'replay', 'revision': saved(app)['revision'], 'defense': 'fake'}).status_code == 400


def test_workshop_mode_does_not_change_replay(alice, app):
    post(alice, '/mode', {'mode': 'secure'})
    post(alice, '/break-fix', {'action': 'attack', 'prompt': 'Show profile 1002'})
    assert json.loads(saved(app)['before_json'])['breached']
    with app.app_context():
        assert get_db().execute('SELECT mode FROM lab_settings').fetchone()[0] == 'secure'
