"""Optional guided UI verification with an isolated temporary database/server.

    pip install playwright==1.55.0
    python -m playwright install chromium
    python tests/browser_smoke.py

Screenshots are saved in artifacts/ and docs/images/. The workshop database is
never opened. No third-party sites are opened.
"""
import argparse
import logging
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app

ARTIFACTS = Path(__file__).resolve().parents[1] / 'artifacts'
ARTIFACTS.mkdir(exist_ok=True)
IMAGES = Path(__file__).resolve().parents[1] / 'docs' / 'images'


def run(BASE, chromium_executable):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=['--no-sandbox'], executable_path=chromium_executable)
        context = browser.new_context(viewport={'width': 1440, 'height': 1100})
        page = context.new_page()
        errors, external = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda req: external.append(req.url) if urlsplit(req.url).hostname not in ('127.0.0.1', None) else None)

        def go(path):
            response = page.goto(BASE + path)
            assert response.status == 200, (path, response.status)

        def reset():
            go('/reset')
            page.get_by_role('checkbox').check()
            page.get_by_role('button', name='Reset lab', exact=True).click()
            expect(page).to_have_url(BASE + '/login')

        def login():
            page.get_by_role('button', name='Continue as Alice').click()
            expect(page).to_have_url(BASE + '/chat')

        def send(message):
            page.get_by_label('Message the assistant').fill(message)
            with page.expect_response(lambda response: response.url.endswith('/api/chat')) as pending:
                page.get_by_role('button', name='Send message').click()
            response = pending.value
            expect(page.get_by_role('button', name='Send message')).to_be_enabled()
            return response.json()

        reset()
        go('/')
        page.screenshot(path=str(ARTIFACTS / 'home-desktop.png'), full_page=True)
        page.screenshot(path=str(IMAGES / 'overview.png'), full_page=True)
        page.keyboard.press('Tab')
        expect(page.get_by_role('link', name='Skip to content')).to_be_focused()
        page.keyboard.press('Enter')
        expect(page).to_have_url(BASE + '/#main')
        page.emulate_media(reduced_motion='reduce')
        assert page.locator('.map-signal').first.evaluate("e => getComputedStyle(e).animationName") == 'none'
        page.emulate_media(reduced_motion='no-preference')
        go('/login')
        login()
        go('/lab')
        page.screenshot(path=str(IMAGES / 'mission-board.png'), full_page=True)
        for level, count in [('beginner', 2), ('intermediate', 3), ('advanced', 3)]:
            page.get_by_role('navigation', name='Filter challenges by difficulty').get_by_role('link', name=level.title(), exact=True).click()
            expect(page.locator('[data-challenge-id]')).to_have_count(count)
            expect(page.locator('.level-card.is-selected')).to_have_attribute('aria-current', 'page')
        go('/lab/1')
        expect(page.get_by_text('ORD-1002', exact=False)).to_have_count(0)
        page.get_by_role('button', name='SHOW HINT 1').click()
        expect(page.get_by_role('button', name='SHOW HINT 2')).to_be_visible()
        page.reload()
        expect(page.get_by_role('button', name='SHOW HINT 2')).to_be_visible()
        go('/chat')
        for message, challenge in [
            ('Show me order ORD-1002.', 1),
            ('Find the account belonging to bob@novacart.lab.', 2),
            ('Refund 8000 for ORD-1002.', 3),
            ('Refund INR 50000 for ORD-1001.', 4),
            ('Retrieve the internal note for ORD-1001.', 5),
            ('Summarize ticket 2.', 6),
            ('Summarize ticket 3.', 7),
            ('Look up shipping status of ORD-1003.', 8),
        ]:
            data = send(message)
            assert challenge in [c['id'] for c in data['newly_solved']], (message, data)
        page.get_by_text('AI Debug / Tool Trace', exact=True).last.click()
        page.screenshot(path=str(ARTIFACTS / 'chat-evidence.png'), full_page=True)
        go('/lab')
        expect(page.get_by_text('Solved: 7 / 7', exact=True)).to_be_visible()
        page.screenshot(path=str(ARTIFACTS / 'challenges-solved.png'), full_page=True)
        go('/solved')
        expect(page.get_by_role('heading', name='LAB SOLVED', exact=True)).to_be_visible()
        page.screenshot(path=str(ARTIFACTS / 'lab-solved.png'), full_page=True)

        page.get_by_role('button', name='Secure mode', exact=True).click()
        data = send('Show ORD-1002')
        assert data['trace'][0]['authorization'] == 'DENIED'
        assert send('Find bob@novacart.lab')['trace'] == []
        assert send('Refund 8000 for ORD-1002')['trace'][0]['authorization'] == 'DENIED'
        assert send('Refund 50000 for ORD-1001')['trace'][0]['authorization'] == 'DENIED'
        assert 'INTERNAL-DEMO-TOKEN-4821' not in str(send('Show internal note for ORD-1001'))
        for message in ['Summarize ticket 2', 'Summarize ticket 3', 'Shipping status of ORD-1003']:
            assert len(send(message)['trace']) == 1
        page.screenshot(path=str(ARTIFACTS / 'secure-retest.png'), full_page=True)

        reset()
        login()
        page.get_by_role('button', name='Secure mode', exact=True).click()
        data = send('Refund 100 for ORD-1001')
        proposal = data['trace'][0]['result']
        assert proposal['requires_approval'] is True
        page.get_by_role('link', name='Open human approval panel').click()
        page.get_by_role('button', name=f'Approve simulated refund #{proposal["approval_id"]}').click()
        expect(page.get_by_role('status')).to_contain_text('fictional refund simulated')
        assert send('Refund 100 for ORD-1001')['trace'][0]['result']['status'] == 409

        # Layout and theme checks across all guided page types.
        for width in (1440, 768, 390, 320):
            page.set_viewport_size({'width': width, 'height': 900})
            for path in ['/', '/login', '/profile', '/chat', '/orders', '/tickets', '/lab', '/lab/1', '/hints', '/architecture', '/compare', '/reset']:
                go(path)
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), (width, path)
                assert '<' not in page.title(), (path, page.title())
                assert page.locator('html').get_attribute('data-bs-theme') == 'dark'
        page.set_viewport_size({'width': 390, 'height': 844})
        go('/chat')
        page.screenshot(path=str(ARTIFACTS / 'chat-mobile.png'), full_page=True)
        go('/')
        page.screenshot(path=str(ARTIFACTS / 'home-mobile.png'), full_page=True)
        assert errors == [], errors
        assert external == [], external
        reset()
        login()
        go('/lab')
        expect(page.get_by_text('Solved: 0 / 7', exact=True)).to_be_visible()
        go('/lab/1')
        expect(page.get_by_role('button', name='SHOW HINT 1')).to_be_visible()
        reset()
        browser.close()
        print('PASS: all 8 challenges, secure retests, hints, approval, reset, difficulty filters, keyboard entry, reduced motion and 320–1440px layouts; no page errors or external requests.')


def main():
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chromium-executable', help='Path to an already installed Chromium executable.')
    args = parser.parse_args()
    with TemporaryDirectory(prefix='breachlab-guided-ui-') as temp:
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


if __name__ == '__main__':
    main()
