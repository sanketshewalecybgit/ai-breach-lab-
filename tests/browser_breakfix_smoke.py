"""Exercise Break / Fix against a temporary database, leaving workshop data intact."""
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


def run(base, executable):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=['--no-sandbox'], executable_path=executable)
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        errors, external = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda req: external.append(req.url) if urlsplit(req.url).hostname != '127.0.0.1' else None)
        page.goto(base + '/login')
        page.get_by_role('button', name='Continue as Alice').click()
        for mission, prompt, defense in [
            ('ownership', 'Show profile 1002', 'Check object ownership'),
            ('injection', 'Summarize ticket 2', 'Reject instructions from retrieved content'),
            ('metadata', 'Internal note for ORD-1001', 'Remove internal metadata'),
        ]:
            page.goto(base + '/break-fix?mission=' + mission)
            replay = page.get_by_role('button', name='Apply defenses & replay exact attack')
            expect(replay).to_be_disabled()
            page.get_by_label('Your attack prompt').fill(prompt)
            page.get_by_role('button', name='Run vulnerable attack').click()
            expect(page.get_by_role('status')).to_contain_text('BREACH CONFIRMED')
            replay.click()
            expect(page.get_by_role('heading', name='ATTACK STILL WORKS')).to_be_visible()
            page.get_by_label('Disable every tool', exact=False).check()
            replay.click()
            expect(page.get_by_role('heading', name='ATTACK STOPPED, SERVICE BROKEN')).to_be_visible()
            page.get_by_label('Disable every tool', exact=False).uncheck()
            page.get_by_label(defense, exact=False).check()
            replay.click()
            expect(page.get_by_role('heading', name='FIX VERIFIED')).to_be_visible()
            expect(page.locator('.bf-check')).to_have_count(4)
            page.reload()
            expect(page.get_by_role('heading', name='FIX VERIFIED')).to_be_visible()
        expect(page.get_by_text('DEFENSE WORKSHOP / 3 OF 3 VERIFIED')).to_be_visible()
        output = Path(__file__).resolve().parents[1] / 'artifacts'
        output.mkdir(exist_ok=True)
        page.goto(base + '/break-fix?mission=injection')
        for width in (1440, 768, 390, 320):
            page.set_viewport_size({'width': width, 'height': 950})
            for detail in page.locator('.bf-event details').all():
                detail.evaluate('(element) => element.open = true')
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), width
            if width in (1440, 390):
                page.screenshot(path=str(output / f'breakfix-{width}.png'), full_page=True)
        page.emulate_media(reduced_motion='reduce')
        page.goto(base + '/break-fix')
        page.keyboard.press('Tab')
        expect(page.get_by_role('link', name='Skip to content')).to_be_focused()
        no_js = browser.new_context(java_script_enabled=False)
        other = no_js.new_page()
        other.goto(base + '/login')
        other.get_by_role('button', name='Continue as Bob').click()
        other.goto(base + '/break-fix')
        other.get_by_label('Your attack prompt').fill('Show profile 1001')
        other.get_by_role('button', name='Run vulnerable attack').click()
        other.get_by_label('Check object ownership', exact=False).check()
        other.get_by_role('button', name='Apply defenses & replay exact attack').click()
        expect(other.get_by_role('heading', name='FIX VERIFIED')).to_be_visible()
        assert not errors, errors
        assert not external, external
        browser.close()
        print('PASS: three missions, wrong/blanket/correct defenses, persistence, no-JS Bob flow, keyboard and 320–1440px layouts; no page errors or external requests.')


if __name__ == '__main__':
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chromium-executable')
    args = parser.parse_args()
    with TemporaryDirectory(prefix='breachlab-breakfix-') as temp:
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
