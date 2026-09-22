# Validation record

## Break / Fix workshop — 2026-09-22

- Added three missions with a vulnerable baseline, individual defense controls,
  server-stored exact attack replay, paired tool traces, and four legitimate-request
  checks. Blocking all tools fails completion. Each execution uses fresh fictional
  fixtures, with progress isolated by identity and mission.
- Full regression suite: **142 passed in 31.26s**, including 11 new tests covering
  both identities, wrong and correct defenses, immutable replay input, restart
  persistence, stale forms, CSRF, escaping, reset, and workshop-state isolation.
- `tests/browser_breakfix_smoke.py`: **PASS** for all three missions, no-defense,
  blanket-block and successful replays, reload persistence, a complete Bob flow
  without JavaScript, keyboard entry, and **320, 390, 768, and 1440px** layouts.
  No page errors or external application requests were observed.
- Desktop/mobile screenshots: `artifacts/breakfix-1440.png` and
  `artifacts/breakfix-390.png`. Tests use temporary databases and servers. The
  normal workshop server remains stopped.

## Scroll-reactive robotic hand — 2026-09-21

- Added original local SVG artwork with five mechanical fingers, palm actuator, wrist, and forearm. A clipped, inert background layer sits beneath the content and cannot intercept clicks or create horizontal overflow.
- Scroll updates use a passive listener and a single queued animation frame, with bounded translation, rotation, and finger flex. Mobile movement is reduced. Reduced-motion preferences disable the scroll listener and restore a static pose, including when changed while the page is open. Artwork remains available without JavaScript.
- **45 application/release tests passed.** The focused motion browser check passed at **1440, 768, 390, and 320 pixels**, including forward/reverse scroll, finger movement, live reduced-motion toggles, keyboard entry, login/chat controls, guided/Expert page layouts, and no-JavaScript rendering. No browser errors, CSP errors, or external requests were observed.
- Desktop/mobile top and scrolled screenshots are in `artifacts/robot-hand-*.png`; the desktop preview is also in `docs/images/robot-hand.png`. The final desktop placement and foreground layering were visually reviewed. The source release was rebuilt; the local application was restarted to load the updated templates. Saved workshop progress was preserved.

## Sci-fi interface and final handoff — 2026-09-21

- Replaced the light theme with a consistent dark operations console: cyan accents, grid background, locally rendered SVG trust-boundary diagram, instrument-style panels, and distinct difficulty/security states. Updated forms, traces, hints, approvals, tables, and the Expert workspace. Animations respect reduced-motion preferences; assets remain offline.
- Full regression suite: **131 passed in 18.21s**. After fixing stray notice markup inside the Architecture page title, the application suite passed again: **44 passed in 5.78s**. Page rendering tests now reject embedded HTML in document titles; the same issue was fixed on the Defensive Version page.
- Guided browser verification: **PASS** for all eight challenges, secure retests, manual hints, human refund approval, resets, difficulty filters, keyboard skip link, and reduced motion. Twelve page types fit at **1440, 768, 390, and 320 pixels**.
- Expert browser verification: **PASS** for all five scenarios, secure retests, hints, approvals, complete evidence download, and fresh-case reset, with **320–1440px** layout checks. Both browser suites reported no JavaScript errors or external application requests.
- Guided browser verification now creates its own temporary SQLite database and localhost server, matching the Expert test's isolation. Verification did not reset workshop data.
- Refreshed `docs/images/overview.png`, `docs/images/mission-board.png`, and guided/Expert screenshots in `artifacts/`. Visually reviewed desktop overview, Expert desktop/mobile, and guided mobile screenshots.
- Rebuilt `dist/ai-breachlab.zip` and checked its integrity and extracted application rendering. Started the normal local lab at `http://127.0.0.1:5000` for review. Docker and remote CI were not run.

## Expert expansion — 2026-09-21

- Python 3.12.3 / Flask 3.1.2 regression suite: **131 passed in 18.62s**.
- Three independently randomized cases each completed all five Expert scenarios from actual backend effects. Secure tests cover reference/integration instructions, cross-tenant search and reads, persisted untrusted memory, exact approval binding, expiry, replay, and live order eligibility. Concurrent secure execution consumes one approval only once.
- Legitimate secure summaries, delivery checks, customer preferences, and eligible approved refunds continue to work. Input validation, escaped reference content, progressive hints, identity isolation, stale forms, resets, and additive storage initialization are covered.
- `tests/browser_expert_smoke.py`: **PASS** for all five scenarios, secure retests, persistent hints, human approvals, evidence download, and fresh-case reset. Layouts passed at **1440, 768, 390, and 320 pixels**. No JavaScript page errors or external application requests were observed.
- Browser checks used Playwright 1.55.0 and the existing local Chromium executable via `--chromium-executable`, with an isolated temporary database/server. They did not open or reset the workshop database.
- Browser verification caught and resolved an HTML form route selecting the JSON endpoint, and long activity status messages overflowing on phones. Reference layout checks explicitly await page load before measuring.
- Screenshots: `artifacts/expert-desktop.png` and `artifacts/expert-mobile.png`. Docker was not built or executed as part of this expansion.

## Current release preparation — 2026-09-17

- Python 3.12 regression suite: **97 passed**. Tests cover all intended attacks and defenses, difficulty filtering, track progress, cross-track evidence, optional challenge counting, reset behavior, and source archive exclusions.
- The extracted clean source archive passed the same **97 tests**, using the installed Python environment. A new dependency installation was not performed.
- Live browser checks passed for 14 views at widths of **1440, 768, 390, and 320 pixels**, with no horizontal page overflow or JavaScript errors.
- Browser interactions verified all three difficulty filters, selected-track indicators, challenge/back navigation, demo login, and GhostStag Security attribution. These checks preserved the live lab's existing progress.
- Source and archive scans found no retired branding. The archive includes GitHub workflow/templates, MIT licensing, documentation, screenshots, application code, and tests. Local databases, environments, logs, agent metadata, and the development brief are excluded.
- New screenshots: [mission board](images/mission-board.png) and [overview](images/overview.png).
- GitHub Actions is configured for Python 3.11, 3.12, and 3.13; remote CI has not run because the repository has not been published. Docker has not been built or executed in this environment.

## Original functional validation — 2026-09-11

Validated on 2026-09-11 using Python 3.12, Flask 3.1.2 and Chromium 140 via Playwright 1.55.0.

- `venv/bin/python -m pytest -q`: **87 passed in 6.60s**.
- Live server: `http://127.0.0.1:5000` returned **HTTP 200**.
- Browser workflow: **PASS** for all eight challenges, seven-core solved screen, server-backed progress and manually revealed persistent hints.
- Vulnerable mode: cross-user order retrieval and customer search, unauthorized and oversized simulated refunds, fictional metadata exposure, ticket injection, chained tools and shipping-output injection all produced the required actual events.
- Secure mode: the same attacks were denied, unavailable, filtered or prevented from initiating injected follow-up calls. Legitimate own-account tools continued to work.
- Approval workflow: eligible refund remained pending until explicit human confirmation; repeat refund was denied.
- Reset: original data/tickets restored, progress and hints cleared, refunds/approvals/logs removed, vulnerable mode restored.
- Desktop (1440px) and mobile (390px) browser layouts checked; no horizontal page overflow in principal pages.
- Browser reported **no JavaScript page errors and no external application requests**.
- Source inspection found no application HTTP client, shell execution, network scanning, payment service or email transport. Only fixed fictional tools are callable.

Screenshots are in `artifacts/`: home desktop/mobile, chat evidence/mobile, solved dashboard, solved screen and secure retest. The browser smoke script is `tests/browser_smoke.py`; its optional dependency installation is documented there. The live lab was reset after verification.

Docker files are provided and reviewed, but the image was **not built or executed** because Docker is not installed in this environment. Its host publication is explicitly limited to loopback; the application binds to all container interfaces only when `--container` is passed.
