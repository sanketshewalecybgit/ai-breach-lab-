"""Verify standalone RAG uploads and retrieval using a temporary database/server."""
import argparse
import json
import logging
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chromium-executable')
    args = parser.parse_args()
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    with TemporaryDirectory(prefix='breachlab-rag-ui-') as temp:
        app = create_app({'DATABASE': str(Path(temp) / 'lab.db'), 'TESTING': True})
        server = make_server('127.0.0.1', 0, app)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{server.server_port}'
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True, executable_path=args.chromium_executable,
                                                     args=['--no-sandbox'])
                context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
                page = context.new_page()
                errors, external = [], []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('request', lambda req: external.append(req.url) if urlsplit(req.url).hostname != '127.0.0.1' else None)

                def evidence():
                    return context.request.get(base + '/rag-poisoning/evidence.json').json()

                def query(words='returns'):
                    page.get_by_label('Search keywords', exact=True).fill(words)
                    page.get_by_role('button', name='Ask the knowledge base', exact=True).click()
                    expect(page).to_have_url(base + '/rag-poisoning#activity')
                    return evidence()['interactions'][-1]

                page.goto(base + '/login')
                page.get_by_role('button', name='Continue as Alice').click()
                page.goto(base + '/lab?level=advanced')
                expect(page.locator('[data-challenge-id]')).to_have_count(5)
                page.locator('[data-challenge-id="10"]').get_by_role('link', name='Start challenge', exact=True).click()
                expect(page.get_by_text('Latest release · 2026-10-12', exact=True)).to_be_visible()
                page.get_by_role('link', name='Open RAG Poisoning lab', exact=False).click()
                expect(page).to_have_url(base + '/rag-poisoning')
                assert '30 days' in query()['answer']
                assert not evidence()['outbox']
                with page.expect_download() as download:
                    page.get_by_role('link', name='download the poisoned reference', exact=True).click()
                sample = Path(download.value.path()).read_bytes()
                page.get_by_label('Reference document', exact=True).set_input_files({
                    'name': 'poisoned-returns.txt', 'mimeType': 'text/plain', 'buffer': sample})
                page.get_by_role('button', name='Upload reference', exact=True).click()
                expect(page).to_have_url(base + '/rag-poisoning#query')
                assert not evidence()['outbox']
                result = query()
                assert result['newly_solved'] and len(evidence()['outbox']) == 1
                expect(page.locator('.study-debrief')).to_have_count(1)
                page.locator('#activity details.trace').first.locator('summary').click()
                page.get_by_role('button', name='SHOW HINT 1', exact=True).click()
                expect(page.get_by_role('button', name='SHOW HINT 2', exact=True)).to_be_visible()
                page.reload()
                expect(page.get_by_role('button', name='SHOW HINT 2', exact=True)).to_be_visible()
                page.get_by_role('button', name='Secure mode', exact=True).click()
                expect(page).to_have_url(base + '/rag-poisoning')
                result = query()
                assert [e['authorization'] for e in result['trace']] == ['ALLOWED', 'DENIED']
                assert len(evidence()['outbox']) == 1
                page.get_by_label('Reference document', exact=True).set_input_files({
                    'name': 'warranty.md', 'mimeType': 'text/markdown', 'buffer': b'Warranty: keep the receipt.'})
                page.get_by_role('button', name='Upload reference', exact=True).click()
                assert len(query('warranty')['trace']) == 1
                with page.expect_download() as download:
                    page.get_by_role('link', name='Download RAG evidence', exact=True).click()
                assert len(json.loads(Path(download.value.path()).read_text())['outbox']) == 1

                artifacts = Path(__file__).resolve().parents[1] / 'artifacts'
                artifacts.mkdir(exist_ok=True)
                for width in (1440, 768, 390, 320):
                    page.set_viewport_size({'width': width, 'height': 1000})
                    for path in ('/lab?level=advanced', '/lab/10', '/rag-poisoning'):
                        page.goto(base + path)
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width, path)
                    if width in (1440, 390):
                        page.screenshot(path=str(artifacts / f'rag-{width}.png'), full_page=True)
                page.get_by_label('Clear my RAG uploads, activity and outbox.').check()
                page.get_by_role('button', name='Clear my RAG workspace', exact=True).click()
                assert not evidence()['outbox'] and not evidence()['interactions']
                expect(page.locator('.study-debrief')).to_have_count(1)  # Completion remains shared.

                # Core upload/query/retest forms also work without JavaScript, as Bob.
                nojs = browser.new_context(java_script_enabled=False)
                other = nojs.new_page()
                other.goto(base + '/login')
                other.get_by_role('button', name='Continue as Bob').click()
                other.goto(base + '/rag-poisoning')
                other.get_by_role('button', name='Vulnerable mode', exact=True).click()
                other.get_by_label('Reference document', exact=True).set_input_files({
                    'name': 'bob-returns.txt', 'mimeType': 'text/plain', 'buffer': sample})
                other.get_by_role('button', name='Upload reference', exact=True).click()
                other.get_by_role('button', name='Ask the knowledge base', exact=True).click()
                expect(other.get_by_role('heading', name='Local review outbox (1)', exact=True)).to_be_visible()
                assert not evidence()['outbox']
                nojs.close()
                assert not errors, errors
                assert not external, external
                browser.close()
                print('PASS: standalone Advanced RAG navigation, sample/upload/query/disclosure, secure and benign retests, hints, evidence, clear, no-JS Bob, 320–1440px layouts; no page errors or external requests.')
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == '__main__':
    main()
