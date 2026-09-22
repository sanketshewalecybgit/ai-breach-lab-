# Contributing to AI BreachLab

AI BreachLab is created and maintained by **GhostStag Security**. Contributions that improve AI security education, accessibility, documentation, and reproducible challenges are welcome.

## Development setup

Use Python 3.11 or newer in a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
python app.py
```

On Windows, use `py -3 -m venv .venv` and `.venv\Scripts\Activate.ps1` in PowerShell. The server runs at `http://127.0.0.1:5000`. Tests use temporary databases and do not reset your live lab.

## Making a change

1. Open an issue for a substantial feature or new scenario.
2. Create a focused branch in your fork.
3. Make the change and update the relevant documentation.
4. Run the regression suite and check desktop/mobile layouts for UI changes.
5. Open a pull request with the problem, resulting behavior, and validation results.

Do not include local databases, virtual environments, real customer information, API keys, or generated logs. The application must work offline after installation; UI assets are served locally.

## Adding challenges

Give each challenge an explicit `difficulty` in `challenges/definitions.py`: `beginner`, `intermediate`, or `advanced`. Beginner lessons focus on single-call access boundaries; Intermediate lessons involve actions, business validation, or context; Advanced lessons follow untrusted content and tool chains.

Each challenge needs a clear objective, three progressive hints, an executed-event success condition, a root cause, and a defensive comparison. Update the evidence engine, seed data, completion counts, and tests together if adding or changing challenge IDs. Never award progress from the user's claim that an attack succeeded.

Keep intentional weaknesses in the vulnerable teaching policy. Preserve independent authorization, schema validation, CSRF protection, and local host restrictions. New tools should act only on fictional local data; do not add arbitrary shell execution or real payment/email integrations.

Expert scenarios live in `expert/`, separately from guided challenge IDs and difficulty filters. Use randomized coherent fixtures and grade relationships and persisted effects rather than specific seed IDs. Preserve provenance across interactions, keep passive reference browsing scoped, and test vulnerable impact, independent secure enforcement, and legitimate task completion. See [Expert implementation notes](docs/expert-instructor-key.md#implementation-and-grading-boundaries).

## Review and security

Break / Fix exercises live in `challenges/breakfix.py`. Each replay must use the
server-stored prompt and fresh identical fixtures, with evidence-based breach
grading and legitimate-request checks. Keep this workspace independent of guided
progress, global mode, and workshop records. Run `python tests/browser_breakfix_smoke.py`
for its optional isolated browser check (supports `--chromium-executable`).

The optional `tests/browser_smoke.py` and `tests/browser_expert_smoke.py` exercises each start an isolated temporary database and localhost server. They never open or reset the workshop database. Both require Playwright and Chromium and accept `--chromium-executable /path/to/chromium`. The guided script also refreshes screenshots in `docs/images/`. Report unintended security issues following [SECURITY.md](SECURITY.md).

The optional `tests/browser_expert_smoke.py` creates its own temporary database and localhost server. With Playwright and Chromium installed, run `python tests/browser_expert_smoke.py` to verify the Expert workflows and layouts without touching workshop data.

Contributions are made under the project's [MIT license](LICENSE). Be respectful, explain tradeoffs, and keep discussions focused on improving the learning experience.
