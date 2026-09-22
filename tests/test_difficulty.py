import re

import pytest

from challenges.definitions import BY_ID, CHALLENGES, LEVELS
from conftest import chat, post


def rendered_ids(response):
    return [int(value) for value in re.findall(r'data-challenge-id="(\d+)"', response.text)]


@pytest.mark.parametrize('level,expected', [
    ('beginner', [1, 2]), ('intermediate', [3, 4, 5]),
    ('advanced', [6, 7, 8]), ('all', list(range(1, 9))),
])
def test_level_filter_shows_only_matching_challenges(client, level, expected):
    response = client.get('/lab', query_string={'level': level})
    assert response.status_code == 200
    assert rendered_ids(response) == expected
    assert 'aria-current="page"' in response.text


def test_default_board_contains_all_challenges(client):
    assert rendered_ids(client.get('/lab')) == list(range(1, 9))


def test_unknown_level_rejected_without_affecting_progress(alice):
    chat(alice, 'Show ORD-1002')
    assert alice.get('/lab?level=unknown').status_code == 400
    assert 'Solved: 1 / 7' in alice.get('/lab').text


def test_expert_opens_its_own_workspace(alice):
    response = alice.get('/lab?level=expert')
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/expert')


def test_challenge_membership_and_navigation(client):
    assert set(LEVELS) == {'beginner', 'intermediate', 'advanced'}
    for challenge in CHALLENGES:
        level = challenge['difficulty']
        assert level in LEVELS
        response = client.get(f'/lab/{challenge["id"]}')
        assert f'/lab?level={level}' in response.text
        assert LEVELS[level]['label'] in response.text
    assert BY_ID[8]['optional'] is True


def test_track_progress_reflects_cross_track_evidence_and_reset(alice):
    # This advanced chain also proves beginner and intermediate weaknesses.
    data = chat(alice, 'Summarize ticket 3').get_json()
    assert {2, 5, 6, 7} <= {item['id'] for item in data['newly_solved']}
    page = alice.get('/lab?level=advanced').text
    assert '1 / 2 solved' in page  # Beginner: customer discovery.
    assert '1 / 3 solved' in page  # Intermediate: internal context.
    assert '2 / 3 solved' in page  # Advanced: injection and chain.
    assert 'Solved: 4 / 7' in page
    assert 'Solved: 4 / 7' in alice.get('/lab?level=beginner').text
    post(alice, '/reset', {'confirm': 'yes'})
    page = alice.get('/lab').text
    assert '0 / 2 solved' in page
    assert page.count('0 / 3 solved') == 2
    assert 'Solved: 0 / 7' in page


def test_optional_advanced_challenge_does_not_change_core_target(alice):
    chat(alice, 'Shipping status of ORD-1003')
    page = alice.get('/lab?level=advanced').text
    assert '1 / 3 solved' in page
    assert '2 core + 1 optional' in page
    # The injected customer lookup also earns core challenge 2, not a second
    # core point for the optional shipping challenge itself.
    assert 'Solved: 1 / 7' in page
    assert alice.get('/solved').status_code == 302
