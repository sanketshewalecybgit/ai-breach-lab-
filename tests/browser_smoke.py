"""Optional live UI verification. WARNING: resets the local lab at start and end.

Start `python app.py` in a separate terminal, then:
    pip install playwright==1.55.0
    python -m playwright install chromium
    python tests/browser_smoke.py

Screenshots are saved in artifacts/. No third-party sites are opened.
"""
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright, expect

BASE = 'http://127.0.0.1:5000'
ARTIFACTS = Path(__file__).resolve().parents[1] / 'artifacts'
ARTIFACTS.mkdir(exist_ok=True)


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=['--no-sandbox'])
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
        go('/login')
        login()
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

        # Mobile navigation and layout: check all principal page widths.
        page.set_viewport_size({'width': 390, 'height': 844})
        for path in ['/', '/chat', '/orders', '/tickets', '/lab', '/hints', '/architecture', '/compare']:
            go(path)
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), path
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
        print('PASS: all 8 challenges, secure retests, manual hints, approval, reset, desktop/mobile layouts; no page errors or external requests.')


if __name__ == '__main__':
    main()
