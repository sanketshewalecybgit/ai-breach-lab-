"""Verify the decorative robotic hand with an isolated database and browser.

Requires Playwright/Chromium. Accepts --chromium-executable for an existing browser.
No workshop data is opened or reset. Screenshots are written to artifacts/.
"""
import argparse
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


def verify(base, executable):
    artifacts = Path(__file__).resolve().parents[1] / 'artifacts'
    artifacts.mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=['--no-sandbox'], executable_path=executable)
        context = browser.new_context(viewport={'width': 1440, 'height': 1000}, reduced_motion='no-preference')
        page = context.new_page()
        errors, external = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
        page.on('request', lambda request: external.append(request.url) if urlsplit(request.url).hostname != '127.0.0.1' else None)
        for width in (1440, 768, 390, 320):
            page.set_viewport_size({'width': width, 'height': 1000 if width == 1440 else 844})
            assert page.goto(base + '/').status == 200
            hand = page.locator('.robot-hand-motion')
            finger = page.locator('.robot-finger').first
            expect(finger).to_have_attribute('transform', 'rotate(0)')
            rest = hand.get_attribute('transform')
            if width in (1440, 390):
                page.screenshot(path=str(artifacts / f'robot-hand-{width}-top.png'))
            page.evaluate("window.scrollTo({top: 650, behavior: 'instant'})")
            expect(hand).not_to_have_attribute('transform', rest)
            expect(finger).not_to_have_attribute('transform', 'rotate(0)')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
            assert page.locator('.robot-backdrop').evaluate("e => getComputedStyle(e).pointerEvents") == 'none'
            assert page.locator('.robot-backdrop').get_attribute('aria-hidden') == 'true'
            if width in (1440, 390):
                page.screenshot(path=str(artifacts / f'robot-hand-{width}-scrolled.png'))
            page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
            expect(hand).to_have_attribute('transform', rest)
            page.emulate_media(reduced_motion='reduce')
            page.evaluate("window.scrollTo({top: 650, behavior: 'instant'})")
            expect(hand).to_have_attribute('transform', rest)
            expect(finger).to_have_attribute('transform', 'rotate(0)')
            # A live preference change resumes at the current position.
            page.emulate_media(reduced_motion='no-preference')
            expect(hand).not_to_have_attribute('transform', rest)
            page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
            expect(hand).to_have_attribute('transform', rest)
        page.keyboard.press('Tab')
        expect(page.get_by_role('link', name='Skip to content')).to_be_focused()
        page.get_by_role('link', name='Launch the lab').click()
        page.get_by_role('button', name='Continue as Alice').click()
        expect(page.get_by_label('Message the assistant')).to_be_editable()
        for path in ('/chat', '/lab', '/expert'):
            assert page.goto(base + path).status == 200
            page.evaluate("window.scrollTo({top: 600, behavior: 'instant'})")
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), path
        # The artwork remains present and decorative without JavaScript.
        static_context = browser.new_context(java_script_enabled=False, reduced_motion='reduce')
        static_page = static_context.new_page()
        static_page.goto(base + '/')
        expect(static_page.locator('.robot-hand')).to_be_visible()
        assert static_page.locator('.robot-hand-motion').get_attribute('transform')
        assert not errors, errors
        assert not external, external
        browser.close()
    print('PASS: scroll/reverse motion, finger articulation, live reduced motion, four widths, keyboard entry, working controls, no-JS fallback; no browser errors or external requests.')


def main():
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chromium-executable')
    args = parser.parse_args()
    with TemporaryDirectory(prefix='breachlab-motion-') as temp:
        app = create_app({'DATABASE': str(Path(temp) / 'lab.db'), 'TESTING': True})
        server = make_server('127.0.0.1', 0, app)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            verify(f'http://127.0.0.1:{server.server_port}', args.chromium_executable)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == '__main__':
    main()
