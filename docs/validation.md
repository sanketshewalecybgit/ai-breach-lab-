# Validation record

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
