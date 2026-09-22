"""Optional Expert UI verification using an isolated temporary database/server.

Requires Playwright and its Chromium browser. Run: python tests/browser_expert_smoke.py
The workshop database is never opened. Screenshots go to artifacts/.
"""
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
from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server


def main():
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chromium-executable', help='Optional path to an already installed Chromium executable.')
    parser.add_argument('--layout-only', action='store_true', help='Check page widths on a fresh case without running the scenario sequence.')
    args = parser.parse_args()
    with TemporaryDirectory(prefix='breachlab-expert-ui-') as temp:
        app = create_app({'DATABASE': str(Path(temp) / 'lab.db'), 'TESTING': True})
        server = make_server('127.0.0.1', 0, app)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{server.server_port}'
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True, args=['--no-sandbox'], executable_path=args.chromium_executable)
                context = browser.new_context(viewport={'width': 1440, 'height': 1000})
                page = context.new_page()
                errors, external = [], []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('request', lambda req: external.append(req.url) if urlsplit(req.url).hostname != '127.0.0.1' else None)

                def evidence():
                    return context.request.get(base + '/expert/evidence.json').json()

                def send(message):
                    page.get_by_label('Task for the assistant').fill(message)
                    page.get_by_role('button', name='Run task').click()
                    expect(page).to_have_url(base + '/expert#activity')
                    return evidence()['interactions'][-1]

                def read_reference(title):
                    page.get_by_role('link', name=title, exact=True).click()
                    page.get_by_role('button', name='Ask the assistant to read this document').click()
                    expect(page).to_have_url(base + '/expert#activity')

                page.goto(base + '/login')
                page.get_by_role('button', name='Continue as Alice').click()
                page.get_by_role('link', name='Expert', exact=True).click()
                expect(page.get_by_role('heading', name='Follow the evidence.')).to_be_visible()
                if args.layout_only:
                    reference = page.get_by_role('link', name='Dispatch reference', exact=True).get_attribute('href')
                    for width in (1440, 768, 390, 320):
                        page.set_viewport_size({'width': width, 'height': 900})
                        for path in ('/', '/lab', '/expert', '/expert/integration', reference):
                            page.goto(base + path)
                            overflow = page.evaluate('''() => ({viewport: innerWidth, root: document.documentElement.scrollWidth,
                                elements: [...document.querySelectorAll('*')]
                                .filter(e => !e.closest('nav.nav-row') && (e.getBoundingClientRect().right > innerWidth || (e.clientWidth > 0 && e.scrollWidth > e.clientWidth + 1)))
                                .slice(0, 30).map(e => ({tag: e.tagName, class: e.className, width: e.clientWidth, scroll: e.scrollWidth,
                                    right: e.getBoundingClientRect().right, text: e.textContent.slice(0, 80)}))})''')
                            assert overflow['root'] <= width, (path, overflow)
                    browser.close()
                    print('PASS: fresh-case layouts at 320–1440px.')
                    return
                order_id = page.locator('#case-file .approval-item strong').first.inner_text()
                case_id = page.locator('input[name="case_id"]').first.input_value()
                page.locator('#mission-memory').get_by_role('button', name='Reveal next hint').click()
                page.reload()
                expect(page.locator('#mission-memory .hint-usage')).to_contain_text('1 / 3')

                read_reference('Dispatch reference')
                assert 'reference' in evidence()['progress']
                read_reference('Agent handover')
                assert 'memory' not in evidence()['progress']
                page.reload()
                send('Prepare support summary')
                assert 'memory' in evidence()['progress']

                result = send('Search documents settlement')
                tenant = evidence()['tenant']
                other = next(d for d in result['trace'][0]['result']['matches'] if d['tenant'] != tenant)
                send(f'Read document {other["id"]}')
                assert 'tenant' in evidence()['progress']
                send(f'Check delivery {order_id}')
                assert 'integration' in evidence()['progress']

                result = send(f'Request refund INR 100 for {order_id}')
                proposal = result['trace'][0]['result']['proposal']['id']
                page.locator('#proposals input[type="checkbox"]').check()
                page.get_by_role('button', name='Approve these details').click()
                expect(page).to_have_url(base + '/expert#proposals')
                send(f'Revise proposal {proposal} to INR 200')
                page.get_by_role('button', name='Execute with assistant').click()
                expect(page).to_have_url(base + '/expert#activity')
                assert len(evidence()['progress']) == 5
                expect(page.get_by_text('5 / 5 objectives confirmed', exact=True)).to_be_visible()

                with page.expect_download() as download:
                    page.get_by_role('link', name='Download evidence', exact=True).click()
                assert len(json.loads(Path(download.value.path()).read_text())['progress']) == 5

                page.get_by_role('button', name='Secure mode', exact=True).click()
                expect(page).to_have_url(base + '/expert')
                prior_exports = len(evidence()['outbox'])
                read_reference('Dispatch reference')
                assert evidence()['interactions'][-1]['trace'][-1]['authorization'] == 'DENIED'
                result = send(f'Check delivery {order_id}')
                assert result['trace'][1]['result']['delivery_status'] == 'delivered'
                assert result['trace'][-1]['authorization'] == 'DENIED'
                result = send(f'Read document {other["id"]}')
                assert result['trace'][0]['authorization'] == 'DENIED'
                result = send('Search documents settlement')
                assert all(d['tenant'] == tenant for d in result['trace'][0]['result']['matches'])
                assert len(evidence()['outbox']) == prior_exports
                result = send('Prepare support summary')
                assert result['trace'][-1]['result']['destination'] == 'customer'
                result = send(f'Execute proposal {proposal}')
                assert result['trace'][0]['authorization'] == 'DENIED'

                artifacts = Path(__file__).resolve().parents[1] / 'artifacts'
                artifacts.mkdir(exist_ok=True)
                page.goto(base + '/expert')
                page.screenshot(path=str(artifacts / 'expert-desktop.png'))
                for width in (1440, 768, 390, 320):
                    page.set_viewport_size({'width': width, 'height': 900})
                    for path in ('/', '/lab', '/expert', '/expert/integration'):
                        page.goto(base + path)
                        fits = page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                        if not fits:
                            overflow = page.evaluate('''() => ({viewport: innerWidth, root: document.documentElement.scrollWidth,
                                elements: [...document.querySelectorAll('*')]
                                .filter(e => !e.closest('nav.nav-row') && (e.getBoundingClientRect().right > innerWidth || (e.clientWidth > 0 && e.scrollWidth > e.clientWidth + 1)))
                                .slice(0, 30).map(e => ({tag: e.tagName, class: e.className, width: e.clientWidth, scroll: e.scrollWidth,
                                    right: e.getBoundingClientRect().right, text: e.textContent.slice(0, 80)}))})''')
                            page.screenshot(path=str(artifacts / 'expert-overflow.png'))
                            raise AssertionError((width, path, overflow))
                    page.goto(base + '/expert')
                    page.get_by_role('link', name='Dispatch reference', exact=True).click()
                    page.wait_for_load_state('load')
                    if not page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'):
                        overflow = page.evaluate('''() => [...document.querySelectorAll('main *')]
                            .filter(e => e.clientWidth > 0 && e.scrollWidth > e.clientWidth + 1)
                            .map(e => ({tag: e.tagName, class: e.className, width: e.clientWidth,
                                scroll: e.scrollWidth, text: e.textContent.slice(0, 120)}))''')
                        page.screenshot(path=str(artifacts / 'expert-reference-overflow.png'))
                        raise AssertionError((width, 'reference', overflow))
                page.goto(base + '/expert')
                page.screenshot(path=str(artifacts / 'expert-mobile.png'))
                page.get_by_label('Replace my current Expert case and its progress.').check()
                page.get_by_role('button', name='Generate a fresh case').click()
                expect(page.get_by_text('0 / 5 objectives confirmed', exact=True)).to_be_visible()
                assert evidence()['case_id'] != case_id
                assert not evidence()['interactions']
                assert not errors, errors
                assert not external, external
                browser.close()
                print('PASS: five Expert scenarios, secure retests, hints, approvals, evidence download, fresh case, 320–1440px layouts; no JS errors or external requests.')
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == '__main__':
    main()
