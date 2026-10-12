"""Check optional learning, debriefs, keyboard access and mobile layout in isolation.

Run: python tests/browser_learning_smoke.py [--chromium-executable /path/to/chrome]
Requires Playwright and Chromium. Uses a temporary database, never workshop state.
"""
import argparse
import logging
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app


def run(base, executable):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=executable, args=['--no-sandbox'])
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='reduce')
        page = context.new_page()
        errors, external = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: external.append(request.url) if urlsplit(request.url).hostname != '127.0.0.1' else None)
        page.goto(base + '/login')
        page.get_by_role('button', name='Continue as Alice').click()
        for path, count in [(f'/lab/{i}', 1) for i in range(1, 10)] + [('/expert', 5)] + [('/break-fix?mission=' + m, 1) for m in ('ownership', 'injection', 'metadata')]:
            page.goto(base + path)
            expect(page.locator('.study-details')).to_have_count(count)
            expect(page.locator('.study-locked')).to_have_count(count)
            expect(page.locator('.study-debrief')).to_have_count(0)
            for card in page.locator('.study-details').all():
                expect(card).not_to_have_attribute('open', '')
                card.locator('summary').focus()
                page.keyboard.press('Enter')
                expect(card).to_have_attribute('open', '')
                expect(card.get_by_role('heading', name='Vocabulary', exact=True)).to_be_visible()
                expect(card.locator('.study-diagram li')).to_have_count(3)
            for width in (1440, 768, 390, 320):
                page.set_viewport_size({'width': width, 'height': 1000})
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (path, width)
        print('PASS: 17 optional learning cards, keyboard expansion and 320–1440px layouts.', flush=True)

        page.goto(base + '/lab/1')
        page.get_by_role('link', name='Jump straight into the exercise').click()
        expect(page).to_have_url(base + '/chat?challenge=1')
        page.get_by_label('Message the assistant').fill('Show order ORD-1002')
        page.get_by_role('button', name='Send message').click()
        page.get_by_role('link', name='Read your after-action debrief').click()
        debrief = page.locator('#debrief-guided-1')
        expect(debrief).to_have_class('study-card study-debrief')
        # Fragment navigation may already expand a native details target.
        if not debrief.evaluate('(element) => element.open'):
            debrief.locator('summary').focus()
            page.keyboard.press('Enter')
        expect(debrief.get_by_role('heading', name='Execution evidence')).to_be_visible()
        expect(debrief).to_contain_text('ORD-1002')
        for width in (1440, 768, 390, 320):
            page.set_viewport_size({'width': width, 'height': 1000})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
        page.set_viewport_size({'width': 1440, 'height': 1000})
        page.locator('.study-details summary').click()
        page.screenshot(path='/tmp/breachlab-learning-desktop.png', full_page=True)
        page.set_viewport_size({'width': 390, 'height': 950})
        page.screenshot(path='/tmp/breachlab-learning-mobile.png', full_page=True)

        # Native learning disclosures and form workspaces also work without JS.
        offline_ui = browser.new_context(java_script_enabled=False, viewport={'width': 320, 'height': 900}, reduced_motion='reduce')
        other = offline_ui.new_page()
        other.goto(base + '/login')
        other.get_by_role('button', name='Continue as Bob').click()
        other.goto(base + '/break-fix?mission=ownership')
        other.locator('.study-details summary').click()
        expect(other.get_by_role('heading', name='Vocabulary')).to_be_visible()
        other.get_by_role('link', name='Jump straight into the exercise').click()
        expect(other).to_have_url(base + '/break-fix?mission=ownership#attack-prompt')
        other.get_by_label('Your attack prompt').fill('Show profile 1001')
        other.get_by_role('button', name='Run vulnerable attack').click()
        expect(other.locator('.study-locked')).to_have_count(1)
        other.get_by_label('Check object ownership', exact=False).check()
        other.get_by_role('button', name='Apply defenses & replay exact attack').click()
        other.locator('.study-debrief summary').click()
        expect(other.get_by_role('heading', name='Take it into a real system')).to_be_visible()
        assert other.evaluate('document.documentElement.scrollWidth <= innerWidth')
        other.goto(base + '/expert')
        other.locator('#learn-expert-reference summary').click()
        other.locator('#mission-reference').get_by_role('link', name='Jump straight into the exercise').click()
        expect(other).to_have_url(base + '/expert#assistant')
        other.goto(base + '/expert#case-file')
        other.get_by_role('link', name='Dispatch reference', exact=True).click()
        other.get_by_role('button', name='Ask the assistant to read this document').click()
        expect(other.locator('.study-locked')).to_have_count(4)
        other.locator('#debrief-expert-reference summary').click()
        expect(other.locator('#debrief-expert-reference').get_by_role('heading', name='Execution evidence')).to_be_visible()
        for width in (1440, 768, 390, 320):
            other.set_viewport_size({'width': width, 'height': 950})
            assert other.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
        assert not errors, errors
        assert not external, external
        browser.close()
        print('PASS: all 17 learning cards, locked answers, solved debrief, keyboard, jump links, no-JS forms, 320–1440px layouts, no page errors or external requests.')


if __name__ == '__main__':
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chromium-executable')
    args = parser.parse_args()
    with TemporaryDirectory(prefix='breachlab-learning-') as temp:
        app = create_app({'DATABASE': str(Path(temp) / 'lab.db'), 'TESTING': True})
        server = make_server('127.0.0.1', 0, app)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            run(f'http://127.0.0.1:{server.server_port}', args.chromium_executable)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
