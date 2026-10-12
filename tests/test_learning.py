"""Debriefs unlock from real persisted outcomes, including isolation and resets."""
from html import escape

import pytest

from challenges.learning import GUIDED, EXPERT, BREAKFIX
from conftest import chat, login, post
from database import get_db
from expert import cases

GUIDED_PROMPTS = {
    1: 'Show order ORD-1002', 2: 'Find bob@novacart.lab',
    3: 'Refund 8000 for ORD-1002', 4: 'Refund 50000 for ORD-1001',
    5: 'Internal note for ORD-1001', 6: 'Summarize ticket 2',
    7: 'Summarize ticket 3', 8: 'Shipping status of ORD-1003',
    9: 'Fetch https://help.novacart.lab/legacy-returns',
}


def assert_debrief(page, lesson, unlocked):
    title = page.text.split('<title>', 1)[1].split('</title>', 1)[0]
    assert '<' not in title and 'debrief' not in title.lower()
    # Check the entire response, not visibility: CSS-hidden answers also fail.
    for value in lesson['debrief'].values():
        assert (escape(value) in page.text) == unlocked


@pytest.mark.parametrize('number,prompt', GUIDED_PROMPTS.items())
def test_guided_learning_unlock_and_reset(alice, app, number, prompt):
    url = f'/lab/{number}'
    page = alice.get(url + '?solved=1&completed=true')
    assert page.status_code == 200
    assert 'Learn before you break' in page.text
    assert 'Jump straight into the exercise' in page.text
    assert 'What to look for' in page.text and 'study-diagram' in page.text
    assert_debrief(page, GUIDED[number], False)
    # Reading lessons, attempting normal work and requesting hints cannot unlock.
    chat(alice, 'Show my profile')
    post(alice, f'/api/hints/{number}', json={})
    assert_debrief(alice.get(url), GUIDED[number], False)
    assert chat(alice, prompt).status_code == 200
    assert_debrief(alice.get(url), GUIDED[number], True)
    post(alice, '/mode', {'mode': 'secure'})
    assert_debrief(alice.get(url), GUIDED[number], True)
    # Guided completion is deliberately shared across demo identities.
    login(alice, 1002)
    assert_debrief(alice.get(url), GUIDED[number], True)
    post(alice, '/reset', {'confirm': 'yes'})
    assert_debrief(alice.get(url), GUIDED[number], False)


def case_state(app):
    with app.app_context():
        return cases.load(get_db(), 1001)


def expert_task(client, app, message):
    response = post(client, '/api/expert/chat', json={'case_id': case_state(app)['id'], 'message': message})
    assert response.status_code == 200
    return response.get_json()


def test_expert_unlocks_individually_and_keeps_identity_scope(alice, app):
    case = case_state(app)
    page = alice.get('/expert?completed=true')
    for lesson in EXPERT.values():
        assert_debrief(page, lesson, False)
    docs = {d['title']: d['id'] for d in case['documents']}
    expert_task(alice, app, f'Read document {docs["Dispatch reference"]}')
    page = alice.get('/expert')
    for mission, lesson in EXPERT.items():
        assert_debrief(page, lesson, mission == 'reference')
    expert_task(alice, app, f'Read document {docs["Agent handover"]}')
    assert_debrief(alice.get('/expert'), EXPERT['memory'], False)
    expert_task(alice, app, 'Prepare support summary')
    search = expert_task(alice, app, 'Search documents settlement')
    assert_debrief(alice.get('/expert'), EXPERT['tenant'], False)
    foreign = next(d for d in search['trace'][0]['result']['matches'] if d['tenant'] != case['tenant'])
    expert_task(alice, app, f'Read document {foreign["id"]}')
    expert_task(alice, app, f'Check delivery {case["orders"][0]["id"]}')
    proposal = expert_task(alice, app, f'Request refund INR 100 for {case["orders"][0]["id"]}')['trace'][0]['result']['proposal']
    assert post(alice, f'/expert/approvals/{proposal["id"]}', {
        'case_id': case['id'], 'confirm': 'yes', 'revision': str(proposal['revision']), 'amount': str(proposal['amount']),
    }).status_code == 302
    expert_task(alice, app, f'Revise proposal {proposal["id"]} to INR 200')
    assert_debrief(alice.get('/expert'), EXPERT['approval'], False)
    expert_task(alice, app, f'Execute proposal {proposal["id"]}')
    post(alice, '/mode', {'mode': 'secure'})
    for lesson in EXPERT.values():
        assert_debrief(alice.get('/expert'), lesson, True)
    login(alice, 1002)
    for lesson in EXPERT.values():
        assert_debrief(alice.get('/expert'), lesson, False)
    login(alice)
    post(alice, '/expert/reset', {'case_id': case['id'], 'confirm': 'yes'})
    for lesson in EXPERT.values():
        assert_debrief(alice.get('/expert'), lesson, False)


@pytest.mark.parametrize('mission,prompt,defense', [
    ('ownership', 'Show profile 1002', 'ownership'),
    ('injection', 'Summarize ticket 2', 'untrusted'),
    ('metadata', 'Internal note for ORD-1001', 'minimize'),
])
def test_breakfix_debrief_requires_verified_useful_fix(alice, app, mission, prompt, defense):
    url = f'/break-fix?mission={mission}'
    lesson = BREAKFIX[mission]
    assert_debrief(alice.get(url + '&passed=true'), lesson, False)
    post(alice, url, {'action': 'attack', 'prompt': prompt})
    assert_debrief(alice.get(url), lesson, False)
    with app.app_context():
        revision = get_db().execute('SELECT revision FROM breakfix_attempts WHERE user_id=1001 AND mission=?', (mission,)).fetchone()[0]
    for controls, unlocked in [([], False), (['deny_all'], False), ([defense], True), ([], False), ([defense], True)]:
        assert post(alice, url, {'action': 'replay', 'revision': revision, 'defense': controls}).status_code == 302
        assert_debrief(alice.get(url), lesson, unlocked)
    login(alice, 1002)
    assert_debrief(alice.get(url), lesson, False)
    login(alice)
    assert_debrief(alice.get(url), lesson, True)
    # A replacement baseline revokes completion, even if the new attack succeeds.
    post(alice, url, {'action': 'attack', 'prompt': prompt})
    assert_debrief(alice.get(url), lesson, False)
    post(alice, '/reset', {'confirm': 'yes'})
    login(alice)
    assert_debrief(alice.get(url), lesson, False)


def test_untrusted_saved_prompt_is_escaped_in_debrief(alice, app):
    prompt = 'Show profile 1002 <script>alert("x")</script>'
    url = '/break-fix?mission=ownership'
    post(alice, url, {'action': 'attack', 'prompt': prompt})
    with app.app_context():
        revision = get_db().execute('SELECT revision FROM breakfix_attempts WHERE user_id=1001').fetchone()[0]
    post(alice, url, {'action': 'replay', 'revision': revision, 'defense': ['ownership']})
    page = alice.get(url)
    assert_debrief(page, BREAKFIX['ownership'], True)
    assert '<script>alert(' not in page.text
    assert escape(prompt, quote=False) in page.text.replace('&#34;', '"')
