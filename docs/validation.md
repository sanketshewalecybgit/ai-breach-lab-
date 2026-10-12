# Validation record

## Standalone Advanced RAG Poisoning Lab — 2026-10-12

- Added optional guided challenge 10 and its independent `/rag-poisoning`
  workspace. Uploads, keyword retrieval, local review outboxes and activity are
  isolated by identity and separate from Expert. Completion and hints use shared
  guided progress; the seven-core solved target remains unchanged. Startup adds
  storage and the progress slot without resetting existing data.
- Retrieval selects the newest reference matching every keyword. Only an actual
  internal export sourced from a retrieved uploaded reference earns completion.
  Secure backend policy denies the export while preserving the same retrieval.
  Bounded text ingestion is shared with the existing Expert upload feature.
- Full regression: **246 passed in 51.87s**. Coverage includes attack evidence,
  secure and benign paths, false-positive prevention, per-identity and Expert
  separation, migration, persistence, clear/full reset, validation, escaping,
  CSRF, stale forms, upload limits, navigation, hints and debrief unlocks.
  Updated the older URL-fetcher homepage assertion to reflect challenge 10
  replacing it as the latest release; the URL mission and its tests remain.
- `tests/browser_rag_smoke.py`: **PASS** for Advanced navigation, sample download,
  upload/query/disclosure, secure and benign retests, hints, evidence download,
  clearing, a no-JavaScript Bob flow, and **320/390/768/1440px** layouts. No page
  errors or external requests. Desktop/mobile screenshots were visually reviewed:
  `artifacts/rag-1440.png` and `artifacts/rag-390.png`.
- Documentation links/anchors checked. Updated README, student and instructor
  material, contributor/security notes and release archive. Tests used temporary
  databases. Browser verification ran outside the sandbox because localhost
  sockets are restricted, and its temporary server shut down after completion.
  The normal workshop server remains stopped and saved workshop data was preserved.

## RAG Poisoning document uploads — 2026-10-12

- Added identity-scoped UTF-8 `.txt`/`.md` ingestion to the Expert knowledge base,
  a downloadable case-specific poisoned sample, and an upload/read/retest walkthrough.
  Uploads use existing keyword retrieval, document provenance, secure enforcement,
  and the reference objective; ingestion alone awards no progress.
- Full regression: **226 passed in 52.04s**. The 18 added checks cover both demo
  identities, sample retrieval and disclosure, secure denial, benign references,
  escaped rendering, invalid formats/encoding/content/size, CSRF, authentication,
  spoofed ownership, stale cases, persistence, resets, and upload count limits.
- `tests/browser_expert_smoke.py`: **PASS** for sample download/upload/search/read,
  all five Expert objectives, secure retests, evidence download and fresh-case reset.
  Workspace and uploaded-document layouts fit at **320, 390, 768 and 1440px**.
  No JavaScript errors or external application requests were observed.
- Browser verification required execution outside the sandbox because localhost
  sockets are restricted. It used a temporary server/database and shut down after
  the checks. The workshop database was not opened and its normal server remains
  stopped. Updated the student/instructor documentation and local source archive.

## Learning cards and after-action debriefs — 2026-09-25

- Added optional concept explanations, vocabulary, intended-flow diagrams and
  observation prompts to all 17 exercises: nine guided, five Expert and three
  Break / Fix. Native disclosures and jump links require no new dependencies.
- Debriefs are gated by persisted server completion and omitted from locked HTML.
  They include saved evidence, trace interpretation, vulnerable design, secure
  behavior, a suggested retest and a practical takeaway. Guided progress remains
  shared; Expert and Break / Fix remain identity-scoped. Break / Fix requires a
  stopped breach and all four legitimate checks; new attacks or failed replays
  revoke its debrief. Resets relock the corresponding material.
- Full regression: **208 passed in 50.04s**, including 14 new checks for actual
  event-based unlocks, locked response contents, per-objective/identity isolation,
  resets, replacement attacks, failed fixes, page-title markup and escaped input.
- `tests/browser_learning_smoke.py` covers all 17 learning cards, keyboard
  expansion, jump links, locked/unlocked content, no-JavaScript form workflows,
  and layouts at **320, 390, 768 and 1440px**. The browser check uses a temporary
  database and localhost server, preserving workshop state. Desktop and mobile
  guided screenshots were visually reviewed. Final browser run: **PASS**,
  including unlocked guided, Expert and Break / Fix debriefs, reduced-motion
  layouts and no-JavaScript Expert/Break / Fix forms; no page errors or external
  requests were observed.
- Updated the complete instructor answer key, Expert instructor key, demo flow,
  student guide, README and the local personal trainer guide. The personal guide
  now includes challenge 9, all three Break / Fix solutions, current counts,
  secure retests and the learning/debrief workflow for all 17 exercises.
- Rebuilt `dist/ai-breachlab.zip`; the packaging script checked archive integrity.

## Assistant URL Fetcher — 2026-09-25

- Added optional Advanced challenge 9, with Latest release labels on the homepage,
  mission board/card, challenge detail and assistant. The fixed virtual catalogue
  includes public pages, a legitimate redirect and a public-to-internal redirect.
- Secure mode checks every destination before reading its fixture, including
  redirect targets. Direct internal reads and redirected internal reads are denied;
  public returns and delivery pages remain available. No HTTP, DNS or host-file I/O
  is used. Both modes retain fixture validation, cycle detection and a four-hop cap.
- Completion requires an executed internal result and proof in the response.
  Guided hints/evidence persist; seven-core completion is unchanged. An additive
  startup migration creates missing progress slots without resetting saved state.
- Full backend regression: **194 passed in 36.00s**. Includes both identities,
  direct/redirected SSRF, public redirects, independent backend enforcement,
  URL parsing and containment, a socket/DNS tripwire, bounded traversal, evidence,
  hint/UI integration, reset and migration preservation.
- Browser verification initially exposed a weakness in the old test selector: it
  clicked the sidebar’s explanatory text instead of the trace summary. The selector
  now targets the actual summary and explicitly asserts that the panel opens.
- Final guided browser verification: **PASS**, all nine challenges, secure retests,
  actual trace expansion, new-mission prefill, hints, approvals and reset. Layouts
  passed at **320, 390, 768 and 1440px** with no page errors or external application
  requests. Visually reviewed the new mission board and the expanded mobile trace.
  Refreshed README overview/mission-board images and `artifacts/url-fetcher-mobile.png`.
- Rebuilt `dist/ai-breachlab.zip` with the new mission, fixtures, tests and docs;
  the packaging tool checked archive integrity.
- All tests use temporary databases; the normal workshop server remains stopped
  and saved workshop data has not been opened or reset.

## Glass interface — 2026-09-22

- Added frosted navigation tabs, reflective panel edges, rounded surfaces, brighter
  body/secondary text, clearer active states, and larger form/chat text. Cyan/violet
  accents, orbital decoration, a slowly rotating trust-boundary ring, and a visual
  Break / Fix path extend the existing operations-console concept.
- Preserved scroll-reactive hand/finger motion. Decorative layers remain inert;
  new motion runs only when reduced motion is not requested. Dark fallback surfaces
  remain readable without backdrop blur; stronger-contrast preferences receive
  brighter text and simpler surfaces.
- Final full suite: **142 passed in 29.11s**. The first run had one session-token
  `KeyError` in an existing Expert approval test (141 passed). Its four-case focused
  rerun and then the full suite passed without backend or test changes.
- Guided, Expert, Break / Fix, and robotic-hand browser suites all passed at
  **320, 390, 768, and 1440px**, including workflows, keyboard entry, no-JS checks,
  scroll reversal, and live reduced-motion changes. No page errors or external
  application requests were reported.
- Foreground palette checks against a representative light panel tone (`#263650`)
  ranged from **6.42:1 to 11.11:1** for body, secondary, navigation, accent, violet,
  and placeholder text. This is a palette check, not a full accessibility audit.
- Visually reviewed desktop overview, mission board, and mobile overview. Refreshed
  `docs/images/overview.png`, `mission-board.png`, and `robot-hand.png`, plus guided,
  Expert, Break / Fix, and motion screenshots in `artifacts/`.
- Restarted the normal lab and verified the updated homepage over localhost.
  Browser verification used temporary databases; saved workshop data was preserved.

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
