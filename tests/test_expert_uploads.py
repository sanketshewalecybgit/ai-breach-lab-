from io import BytesIO

import pytest

from conftest import csrf, login, post
from database import get_db
from expert import cases
from test_expert import state, task


def upload(client, case, content=b'Ordinary dispatch guidance.', filename='reference.txt', **extra):
    return post(client, '/expert/documents/upload', {
        'case_id': case['id'], 'document': (BytesIO(content), filename), **extra})


@pytest.mark.parametrize('actor', [1001, 1002])
def test_uploaded_sample_retrieval_attack_and_secure_retest(client, app, actor):
    login(client, actor)
    case = state(app, actor)
    sample = client.get(f'/expert/cases/{case["id"]}/poison-sample.txt')
    assert sample.status_code == 200
    assert 'attachment;' in sample.headers['Content-Disposition']
    assert b'FICTIONAL-INTERNAL' not in sample.data
    response = upload(client, case, sample.data, 'rag-poisoning-sample.txt',
                      tenant='spoofed', classification='internal', actor='1002')
    assert response.status_code == 302
    document = state(app, actor)['documents'][-1]
    assert document['tenant'] == case['tenant'] and document['classification'] == 'customer'
    assert client.get(response.location).status_code == 200
    assert not state(app, actor)['outbox'] and not state(app, actor)['progress']

    def run(message):
        return post(client, '/api/expert/chat', json={'case_id': case['id'], 'message': message}).get_json()

    search = run('Search documents rag')
    assert document['id'] in [d['id'] for d in search['trace'][0]['result']['matches']]
    assert not search['newly_solved']
    result = run(f'Read document {document["id"]}')
    read, export = result['trace']
    assert export['source'] == {'kind': 'document', 'id': document['id'], 'event_id': read['id']}
    assert export['result']['destination'] == 'review'
    assert result['newly_solved'][0]['id'] == 'reference'
    evidence = client.get('/expert/evidence.json').get_json()
    assert evidence['interactions'][0]['trace'][0]['tool'] == 'upload_document'
    assert evidence['interactions'][0]['trace'][0]['result']['body'] == document['body']
    assert len(evidence['outbox']) == 1
    post(client, '/mode', {'mode': 'secure'})
    result = run(f'Read document {document["id"]}')
    assert [e['authorization'] for e in result['trace']] == ['ALLOWED', 'DENIED']
    assert len(state(app, actor)['outbox']) == 1
    assert not state(app, 1002 if actor == 1001 else 1001)['outbox']


@pytest.mark.parametrize('mode', ['vulnerable', 'secure'])
def test_benign_upload_and_escaped_content(alice, app, mode):
    post(alice, '/mode', {'mode': mode})
    body = '\ufeff# Shipping café\n<script>alert(1)</script>\nUseful guidance.'
    response = upload(alice, state(app), body.encode(), '../../shipping.MD')
    assert response.status_code == 302
    document = state(app)['documents'][-1]
    assert document['filename'] == 'shipping.MD'
    assert document['body'].startswith('# Shipping café')
    page = alice.get(response.location)
    assert '<script>alert(1)</script>' not in page.text
    assert '&lt;script&gt;' in page.text
    result = task(alice, app, f'Read document {document["id"]}')
    assert len(result['trace']) == 1 and result['trace'][0]['authorization'] == 'ALLOWED'
    assert not result['newly_solved'] and not state(app)['outbox']


@pytest.mark.parametrize('filename,content', [
    ('document.pdf', b'%PDF'), ('document.docx', b'PK'), ('document', b'hello'),
    ('document.txt.exe', b'hello'), ('empty.txt', b' \n'), ('binary.txt', b'a\x00b'),
    ('invalid.txt', b'\xff'), ('long.md', b'x' * 4001), ('large.txt', b'x' * 12289),
    ('control.txt', b'a\x1bb'), ('', b'hello'),
])
def test_upload_rejects_invalid_documents_without_mutating(alice, app, filename, content):
    before = state(app)
    assert upload(alice, before, content, filename).status_code == 400
    assert state(app) == before
    assert not alice.get('/expert/evidence.json').get_json()['interactions']


def test_upload_auth_csrf_missing_file_and_body_limit(client, app):
    case = state(app)
    assert upload(client, case).status_code == 302
    assert state(app) == case
    login(client)
    assert client.post('/expert/documents/upload', data={
        'case_id': case['id'], 'document': (BytesIO(b'text'), 'a.txt')}).status_code == 400
    assert post(client, '/expert/documents/upload', {'case_id': case['id']}).status_code == 400
    assert upload(client, case, b'a' * 20000).status_code == 413
    assert client.post('/expert/documents/upload', data={
        'case_id': case['id'], 'csrf_token': csrf(client),
        'document': [(BytesIO(b'a'), 'a.txt'), (BytesIO(b'b'), 'b.txt')]}).status_code == 400
    assert state(app) == case


def test_upload_isolation_stale_case_persistence_and_reset(alice, app):
    case = state(app)
    other_case = state(app, 1002)
    assert upload(alice, other_case).status_code == 409
    assert alice.get(f'/expert/cases/{other_case["id"]}/poison-sample.txt').status_code == 409
    response = upload(alice, case)
    document = state(app)['documents'][-1]
    with app.app_context():
        cases.initialize(get_db())
    assert state(app)['documents'][-1] == document
    login(alice, 1002)
    assert alice.get(response.location).status_code == 404
    assert 'reference.txt' not in alice.get('/expert/evidence.json').text
    assert document['id'] not in alice.get('/expert').text
    login(alice)
    post(alice, '/expert/reset', {'case_id': case['id'], 'confirm': 'yes'})
    assert upload(alice, case).status_code == 409
    assert alice.get(f'/expert/cases/{case["id"]}/poison-sample.txt').status_code == 409
    assert alice.get(response.location).status_code == 404
    assert not any(d.get('uploaded') for d in state(app)['documents'])
    assert not alice.get('/expert/evidence.json').get_json()['interactions']
    assert state(app, 1002) == other_case


def test_upload_limit_and_distinct_ids_for_duplicate_filenames(alice, app):
    case = state(app)
    for _ in range(20):
        assert upload(alice, case).status_code == 302
    before = state(app)
    documents = [d for d in before['documents'] if d.get('uploaded')]
    assert len({d['id'] for d in documents}) == 20
    assert upload(alice, case).status_code == 400
    assert state(app) == before
