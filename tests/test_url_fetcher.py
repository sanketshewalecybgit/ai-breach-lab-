"""Exercise SSRF effects, destination enforcement, containment and upgrades."""
import json
import socket

import pytest

from app import create_app
from conftest import chat, login, post
from database import get_db
from tools import execute
from tools import url_tools

PUBLIC = 'https://help.novacart.lab'
INTERNAL = 'http://ops.novacart.lab/diagnostics'


@pytest.mark.parametrize('user', [1001, 1002])
@pytest.mark.parametrize('url', [INTERNAL, PUBLIC + '/legacy-returns'])
def test_internal_fetch_proves_optional_challenge_and_persists_events(client, app, user, url):
    login(client, user)
    response = chat(client, f'Fetch {url}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['trace'][0]['tool'] == 'fetch_url'
    assert data['trace'][0]['authorization'] == 'NOT CHECKED'
    result = data['trace'][0]['result']
    assert result['classification'] == 'internal'
    assert result['final_url'] == INTERNAL
    assert url_tools.PROOF in result['body'] and url_tools.PROOF in data['response']
    assert result['hops'][-1]['outcome'] == 'RETRIEVED'
    assert [item['id'] for item in data['newly_solved']] == [9]
    assert data['solved_count'] == 0
    assert client.get('/solved').status_code == 302
    with app.app_context():
        db = get_db()
        saved = db.execute('SELECT tool_result FROM tool_events WHERE interaction_id=?', (data['interaction_id'],)).fetchone()
        assert json.loads(saved[0]) == result
        assert db.execute('SELECT solved FROM challenge_progress WHERE challenge_id=9').fetchone()[0] == 1
    assert not chat(client, f'Fetch {url}').get_json()['newly_solved']


@pytest.mark.parametrize('url', [INTERNAL, PUBLIC + '/legacy-returns'])
def test_secure_checks_destination_before_reading_internal_page(secure, monkeypatch, url):
    class PublicPagesOnly(dict):
        def get(self, key, default=None):
            assert key != INTERNAL, 'Internal content must not even be read'
            return super().get(key, default)

    monkeypatch.setattr(url_tools, 'PAGES', PublicPagesOnly(url_tools.PAGES))
    response = chat(secure, f'Fetch {url}')
    assert response.status_code == 403
    data = response.get_json()
    event = data['trace'][0]
    assert event['authorization'] == 'DENIED'
    assert event['result']['hops'][-1] == {'url': INTERNAL, 'policy': 'DENIED', 'outcome': 'BLOCKED'}
    assert len(event['result']['hops']) == (1 if url == INTERNAL else 2)
    assert 'body' not in event['result']
    assert url_tools.PROOF not in response.text
    assert not data['newly_solved']


@pytest.mark.parametrize('mode', ['vulnerable', 'secure'])
@pytest.mark.parametrize('path,final,hops', [('/returns', '/returns', 1), ('/delivery', '/shipping', 2)])
def test_legitimate_pages_and_public_redirects_stay_useful(alice, mode, path, final, hops):
    post(alice, '/mode', {'mode': mode})
    response = chat(alice, f'Fetch {PUBLIC}{path}.')
    assert response.status_code == 200
    data = response.get_json()
    result = data['trace'][0]['result']
    assert result['classification'] == 'public'
    assert result['final_url'] == PUBLIC + final
    assert len(result['hops']) == hops
    assert not data['newly_solved']
    assert all(hop['policy'] == ('ALLOWED' if mode == 'secure' else 'NOT CHECKED') for hop in result['hops'])


@pytest.mark.parametrize('url', [
    'https://example.com', 'http://127.0.0.1/', 'http://169.254.169.254/',
    'file:///etc/passwd', 'ftp://help.novacart.lab/returns',
    'https://help.novacart.lab.evil.test/returns',
    'https://help.novacart.lab@ops.novacart.lab/diagnostics',
    'https://user:pass@help.novacart.lab/returns',
    'https://%68elp.novacart.lab/returns', 'https://help.novacart.lab:abc/returns',
    'https://help.novacart.lab:5000/returns', 'https://[bad/returns',
    'https://help.novacart.lab\\@ops.novacart.lab/diagnostics',
    'https://help.novacart.lab/returns?next=/diagnostics',
    'https://help.novacart.lab/returns#fragment',
    'https://help.novacart.lab/ret\nurns',
])
@pytest.mark.parametrize('mode', ['secure', 'vulnerable'])
def test_fixture_boundary_rejects_arbitrary_or_ambiguous_urls(app, url, mode):
    with app.app_context():
        result, authorization = execute(get_db(), {'id': 1001, 'role': 'customer'}, mode, 'fetch_url', {'url': url})
    assert authorization == 'SCHEMA REJECTED'
    assert result['status'] == 400


def test_no_network_io_in_any_mode(alice, monkeypatch):
    def unexpected_network(*args, **kwargs):
        pytest.fail('Virtual URL fetcher attempted a network operation')

    monkeypatch.setattr(socket, 'socket', unexpected_network)
    monkeypatch.setattr(socket, 'getaddrinfo', unexpected_network)
    for mode in ('vulnerable', 'secure'):
        post(alice, '/mode', {'mode': mode})
        for url in (PUBLIC + '/returns', PUBLIC + '/legacy-returns', PUBLIC + '/missing', 'https://example.com'):
            assert chat(alice, f'Fetch {url}').status_code in (200, 400, 403, 404)


@pytest.mark.parametrize('mode', ['vulnerable', 'secure'])
def test_redirect_escape_is_contained_even_in_vulnerable_mode(alice, monkeypatch, mode):
    monkeypatch.setitem(url_tools.PAGES, PUBLIC + '/delivery', {'location': 'https://example.com'})
    post(alice, '/mode', {'mode': mode})
    response = chat(alice, f'Fetch {PUBLIC}/delivery')
    assert response.status_code == 400
    assert response.get_json()['trace'][0]['result']['hops'][-1]['outcome'] == 'REJECTED'


def test_redirect_loop_and_hop_budget_are_bounded(alice, monkeypatch):
    monkeypatch.setitem(url_tools.PAGES, PUBLIC + '/delivery', {'location': '/delivery'})
    response = chat(alice, f'Fetch {PUBLIC}/delivery')
    assert response.status_code == 422
    assert response.get_json()['trace'][0]['result']['hops'][-1]['outcome'] == 'REDIRECT LOOP'
    for i in range(6):
        monkeypatch.setitem(url_tools.PAGES, PUBLIC + f'/hop-{i}', {'location': f'/hop-{i + 1}'})
    result = chat(alice, f'Fetch {PUBLIC}/hop-0').get_json()['trace'][0]['result']
    assert result['status'] == 422
    assert len(result['hops']) == url_tools.MAX_HOPS
    assert 'body' not in result


def test_backend_enforces_policy_without_the_parser(app):
    with app.app_context():
        user = {'id': 1001, 'role': 'customer'}
        result, authorization = execute(get_db(), user, 'secure', 'fetch_url', {'url': PUBLIC + '/legacy-returns'})
        assert result['status'] == 403 and authorization == 'DENIED'
        result, authorization = execute(get_db(), user, 'secure', 'fetch_url', {'url': PUBLIC + '/returns'}, source='ticket:2')
        assert result['status'] == 403 and authorization == 'DENIED'


def test_unknown_page_claims_and_multiple_urls_do_not_solve(alice):
    assert chat(alice, f'Fetch {PUBLIC}/unknown').status_code == 404
    assert not chat(alice, f'I retrieved {url_tools.PROOF}').get_json()['newly_solved']
    data = chat(alice, f'Fetch {PUBLIC}/returns and {INTERNAL}').get_json()
    assert not data['trace'] and not data['newly_solved']


def test_latest_release_ui_hints_and_prefill(alice):
    for path in ('/', '/lab', '/lab/9', '/chat'):
        page = alice.get(path).text
        assert 'Latest release' in page and 'Assistant URL Fetcher' in page
        assert url_tools.PROOF not in page
    assert 'ops.novacart.lab' not in alice.get('/lab/9').text
    assert f'Fetch {PUBLIC}/returns</textarea>' in alice.get('/chat?challenge=9').text
    for count in (1, 2, 3):
        data = post(alice, '/api/hints/9', json={}).get_json()
        assert data['hints_used'] == count
    assert 'legacy-returns' in data['hints'][-1]
    assert 'legacy-returns' in alice.get('/lab/9').text


def test_upgrade_keeps_existing_data_and_adds_progress_slot(alice, app):
    chat(alice, 'Show ORD-1002')
    post(alice, '/api/hints/1', json={})
    post(alice, '/tickets', {'subject': 'Keep me', 'message': 'Saved workshop ticket'})
    post(alice, '/mode', {'mode': 'secure'})
    with app.app_context():
        db = get_db()
        cases = [tuple(row) for row in db.execute('SELECT * FROM expert_cases ORDER BY actor')]
        db.execute('DELETE FROM challenge_progress WHERE challenge_id=9')
        db.commit()
    upgraded = create_app({'TESTING': True, 'DATABASE': app.config['DATABASE']})
    with upgraded.app_context():
        db = get_db()
        assert db.execute('SELECT solved, hints_used FROM challenge_progress WHERE challenge_id=1').fetchone()[:] == (1, 1)
        assert db.execute('SELECT solved, hints_used FROM challenge_progress WHERE challenge_id=9').fetchone()[:] == (0, 0)
        assert db.execute('SELECT mode FROM lab_settings').fetchone()[0] == 'secure'
        assert db.execute("SELECT COUNT(*) FROM support_tickets WHERE subject='Keep me'").fetchone()[0] == 1
        assert [tuple(row) for row in db.execute('SELECT * FROM expert_cases ORDER BY actor')] == cases


def test_reset_clears_url_progress_and_reseeds_ninth_slot(alice, app):
    chat(alice, f'Fetch {INTERNAL}')
    post(alice, '/api/hints/9', json={})
    assert post(alice, '/reset', {'confirm': 'yes'}).status_code == 302
    with app.app_context():
        db = get_db()
        assert db.execute('SELECT solved, hints_used FROM challenge_progress WHERE challenge_id=9').fetchone()[:] == (0, 0)
        assert db.execute("SELECT COUNT(*) FROM tool_events WHERE tool_name='fetch_url'").fetchone()[0] == 0
