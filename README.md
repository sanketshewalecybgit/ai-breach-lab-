# AI BreachLab

**Advanced AI Attack Surfaces · Created by GhostStag Security**

**Beginner → Intermediate → Advanced → Expert** · 8 guided challenges + 5 Expert investigations + 3 Break / Fix missions · No API keys

[Quick start](#requirements-and-installation) · [Difficulty levels](#difficulty-levels) · [Contributing](CONTRIBUTING.md) · [MIT license](LICENSE)

AI BreachLab is an independent contribution to AI security education: an intentionally vulnerable, hands-on training environment. Its NovaCart Support scenario connects a fictional customer support assistant to customer data and business tools. Deterministic mock agents convert supported tasks into fictional tool calls. Students inspect actual backend events, complete seven core challenges and one advanced challenge, then investigate five randomized Expert scenarios and retest in secure mode.

> This project is an intentionally vulnerable educational application. Run it only on localhost or an isolated training environment. Do not expose it publicly.

![AI BreachLab mission dashboard with three difficulty tracks](docs/images/mission-board.png)

## Learning objectives

Explore authentication versus authorization, broken object-level authorization (BOLA), model-selected tool parameters, excessive agency, business-rule validation, sensitive context exposure, indirect prompt injection, and chained attacks. The central lesson: **the model is not the security boundary**.

## Requirements and installation

Python 3.11+ and pip. Python 3.12 is validated locally; CI is configured for 3.11, 3.12, and 3.13. Download or clone this repository and open a terminal in its root directory. No AI account, paid API, API key, password, Node.js, or external database is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** and choose Alice to begin. Stop the server with `Ctrl+C`.

On Windows PowerShell:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe app.py
```

Dependencies require a one-time package download. Bootstrap CSS is bundled locally with its license. The running application makes no external requests and works offline.

## Demo identities

Select Alice (1001, `alice@novacart.lab`) or Bob (1002, `bob@novacart.lab`) at `/login`. No passwords are accepted or needed. Start as Alice. Admin Demo (9001) is fictional seed data, not a selectable login identity. Use only fictional information in messages and tickets.

Each local instance is intended for **one student**. Guided database state, progress, hints and mode are shared across identity changes and browser sessions. Expert gives Alice and Bob separate randomized cases and progress; the security mode remains shared. Different students should run separate instances. The session signing key is randomly generated at startup; a server restart requires selecting an identity again while saved lab progress remains.

## Difficulty levels

Choose a track on the homepage or filter the mission board at `/lab`. Each level shows its own saved completion count.

| Level | Challenges | What you investigate |
|---|---|---|
| **Beginner** | 1–2 | Identity, ownership, and tools with excessive access |
| **Intermediate** | 3–5 | Unauthorized actions, invalid amounts, and sensitive context |
| **Advanced** | 6–8 | Indirect injection, multi-step tool chains, and untrusted tool output |
| **Expert** | 5 independent objectives | Randomized case discovery, persistent effects, tenant isolation, and approval integrity |

Beginner, Intermediate, and Advanced are curated difficulty tracks, not a switch that changes an attack's backend behavior. **Expert** opens a separate workspace at `/expert` with new data, tools, persistent workflows, and independent grading. Every track is available immediately. All challenges retain three optional progressive hints. Vulnerable/secure mode is a separate control for comparing attacks with defenses.

Track progress includes every challenge in that track, including optional challenge 8 in Advanced. Overall lab completion requires only the seven core challenges. An executed chain can solve multiple challenges across tracks; filtering never changes or clears saved progress.

## Break it, then fix it

Choose **Break / Fix** in the navigation or mission board to practice three missions:
cross-account access, ticket-based prompt injection, and internal metadata exposure.
Run an attack, select individual defenses, and replay the exact saved prompt. Compare
the before/after tool traces and four legitimate-request checks. Disabling every tool
stops an attack but fails the exercise because customers lose useful functionality.

Each run uses a fresh, isolated fictional database and the existing deterministic
parser and tools. Defense controls apply only to this workspace, independently of
the global mode switch. Progress persists separately for Alice and Bob; a new attack
replaces that mission’s result, and full lab reset clears all Break / Fix progress.
Existing installations gain its storage automatically at startup. Verification
covers the saved attack and the displayed checks, not arbitrary attacks or real LLMs.

## Expert investigations

Choose **Expert** in the navigation or on the mission board. Each case has randomized fictional company/customer IDs, orders, document IDs, amounts, and confidential content. Students start from a business brief and discover clues through case references and the assistant’s document catalogue. Vulnerability names and explanations unlock after actual evidence confirms an objective.

The five deeper scenarios cover knowledge-base poisoning, persistent memory contamination across interactions, cross-tenant document retrieval, approval tampering/replay, and tool-description manipulation. Students can edit selected reference documents and a fictional integration description. Exports go only to local customer/review outboxes; refunds are database simulations.

Expert provides source-linked traces, progressive hints, an explicit approval desk, persisted activity, and downloadable evidence. Its five-objective progress is independent of the seven-core solved screen. A confirmed fresh-case action randomizes only the current identity’s Expert workspace and retains the current security mode. See the [Expert student guide](docs/expert-guide.md) and [instructor key (spoilers)](docs/expert-instructor-key.md).

The Expert agent is also deterministic, with documented task forms and a small editable-content directive grammar. It is not a real-model benchmark. It executes at most six tools per interaction. Secure mode independently blocks unauthorized effects while allowing legitimate summaries, delivery checks, and approved refunds, including when untrusted memory survives from vulnerable mode.

Existing installations gain Expert storage automatically at startup without resetting guided data. Restart the server after updating the source.

## Challenges

| # | Difficulty | Challenge | Concept |
|---|---|---|---|
| 1 | Beginner | Whose Data Is It? | Broken object-level authorization |
| 2 | Beginner | Should the AI Have This Tool? | Excessive agency |
| 3 | Intermediate | Refund Anything? | Unauthorized simulated refund |
| 4 | Intermediate | Valid JSON Does Not Mean Valid Action | Parameter manipulation |
| 5 | Intermediate | What Entered the Model Context? | Sensitive-data exposure |
| 6 | Advanced | Data or Instruction? | Ticket-based indirect prompt injection |
| 7 | Advanced | One Result Leads to Another | Unsafe tool chain |
| 8 | Advanced · optional | Tool Output Injection | Shipping-output injection |

Go to `/lab` for objectives and progress. Hints reveal manually and record usage without reducing a score. Progress comes from executed tool results on the server; text claiming success cannot solve a challenge. Completing challenges 1–7 unlocks `/solved`.

## Using the agent

Open `/chat` and send one task per message. The mock parser supports profile, order, customer-email lookup, refund, internal note, ticket, ticket creation and shipping intents. Include an object identifier where relevant. Refund amounts are **whole-number INR**, not paise. Inspect the collapsible **AI Debug / Tool Trace** after each response. Parser decision labels are explanatory state, not actual LLM reasoning.

The agent uses fixed intent rules, not a general-purpose language model. It does not obey arbitrary instructions. In vulnerable mode, retrieved ticket or carrier text containing a recognized `AI SUPPORT AGENT` / `AI assistant` marker can intentionally propose the allowlisted follow-up tools. This makes the injection exercise reproducible and supports student-created tickets; it is not a claim that real LLM behavior follows these exact rules. Each interaction has a finite four-call limit. Chat display is in-memory for the current page; executed tool events persist in SQLite.

## Secure mode

Use the mode toggle or `/compare`. Secure mode:

- Binds profile, order, ticket and note access to the authenticated customer.
- Removes global search from customer tool lists and rejects it in independent backend policy.
- Checks refund ownership, positive amount, amount paid, prior refund status and delivered status.
- Creates an approval proposal for an eligible refund; nothing is refunded until a human explicitly confirms.
- Revalidates ownership and current business rules inside a write transaction when approval is confirmed.
- Removes internal debug metadata before tool results enter agent context.
- Treats retrieved ticket/shipping text as data and rejects tool transitions sourced from that content.

The approval panel is a **local human-confirmation demonstration**, not a separate manager authentication system. Both modes apply structural validation and fixed tool allowlists. The vulnerable policy intentionally skips semantic authorization/business checks. Secure mode does not erase earlier evidence or undo earlier fictional refunds. Reset first if a prior refund would affect a demonstration.

## Reset

Open `/reset`, check **Yes, reset all lab progress**, then press **Reset lab**. This restores users, orders, notes and original tickets; removes refunds, approvals and tool logs; clears progress/hints; replaces both Expert cases and their evidence; restores vulnerable mode; and clears the current login. A GET request never resets data. Stop active requests before resetting a shared demonstration instance.

## Docker (optional)

```bash
docker compose up --build
```

Open the same localhost URL. Stop with `docker compose down`. The named volume retains lab state; use the application reset to restore it. The internal Docker network restricts container egress, and the published port is explicitly `127.0.0.1:5000:5000`.

Docker stores only SQLite data in `/lab/data`, configured through `NOVACART_DATABASE`; Python source remains part of the image. The normal local database path is `database/lab.db`.

Inside Docker only, `--container` binds to `0.0.0.0` so port publication works. Normal `python app.py` binds exclusively to `127.0.0.1`. Do not use `--container` directly on a host. Docker starts as an unprivileged user with dropped capabilities. Docker requires internet access when building the image; application runtime does not.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests use isolated temporary SQLite databases, not your workshop database. They prove vulnerable attacks work, secure defenses work, tools remain useful, actual events drive progress, approvals revalidate state, hints remain progressive, and reset restores the original lab. `tests/browser_smoke.py` is an optional browser smoke test; instructions are in that file. It starts its own temporary database and localhost server, preserving workshop progress.

`tests/browser_expert_smoke.py` verifies the five Expert scenarios and secure retests through a browser using its own temporary database and localhost server. It requires Playwright with Chromium and does not open or reset your workshop database.

Both browser scripts accept `--chromium-executable /path/to/chromium` to use an existing browser. They check responsive layouts at 320, 390, 768, and 1440 pixels. The guided script also verifies keyboard entry, reduced-motion support, difficulty filters, and refreshes the screenshots in `docs/images/`. The sci-fi interface uses locally bundled CSS, system fonts, and an SVG trust-boundary illustration; it needs no external assets.

A decorative SVG robotic hand lifts, rotates, and gently flexes its fingers as the page scrolls. It stays behind the content, uses subtler movement on phones, and remains still when reduced motion is enabled. `tests/browser_motion_smoke.py` verifies scroll reversal, live motion preferences, mobile layouts, keyboard access, and the no-JavaScript fallback with an isolated database. It accepts the same `--chromium-executable` option. [View the robotic-hand preview](docs/images/robot-hand.png).

## Architecture and source map

```text
app.py                     Flask pages, session/CSRF handling, API, mode and reset
config.py                  Local paths and fictional token
ai/                        Provider interface, deterministic mock and agent loop
tools/                     Fixed fictional backend tools and dispatcher
security/                  Vulnerable and secure policies
challenges/                Challenge definitions and server-side evidence engine
expert/                    Randomized cases, Expert tools/policy, agent, grading and routes
database/                  Schema and seed data (local lab.db is ignored)
templates/                 Jinja2 student portal
static/                    Local Bootstrap CSS, custom CSS and vanilla JavaScript
tests/                     Vulnerability, defense and application regression tests
docs/                      Guides, screenshots, and publishing instructions
scripts/package_release.py Clean source archive builder
.github/                   CI workflow and issue/PR templates
Dockerfile
docker-compose.yml
requirements.txt
```

No real credentials or service integrations exist. The only educational secret is a clearly fictional internal demo token. There is no shell execution, HTTP client, network scanner, user-selected host, payment gateway or email transport in application code. SQL uses parameterized values; HTML/text is escaped. Local host validation, CSRF tokens and a restrictive content security policy protect the classroom boundary without fixing the intended AI vulnerabilities.

## Workshop materials

- Student guide: [docs/student-guide.md](docs/student-guide.md)
- Instructor answer key (spoilers), including all guided challenges and Break / Fix solutions: [docs/instructor-answer-key.md](docs/instructor-answer-key.md)
- 30-minute guided delivery sequence and 20-minute Break / Fix extension: [docs/instructor-demo-flow.md](docs/instructor-demo-flow.md)
- Expert student guide: [docs/expert-guide.md](docs/expert-guide.md)
- Expert instructor key and 60–90 minute session: [docs/expert-instructor-key.md](docs/expert-instructor-key.md)

## Troubleshooting

- **Missing Flask:** activate the virtual environment and rerun `python -m pip install -r requirements.txt`.
- **Port 5000 in use:** stop the existing local lab/server before starting another copy.
- **403 in secure mode:** inspect the trace; denial may be the expected fix working.
- **202 for a refund:** it is an unexecuted approval proposal. Reload the assistant to see the human approval panel.
- **Prompt not understood:** use one supported task with an order ID/ticket number. See the parser limits above; this is a deterministic simulator.
- **CSRF error after login/reset in another tab:** reload the tab to get the current form token.
- **Progress is already solved:** progress is shared within one instance. Reset for a fresh workshop.
- **Write permission error:** the database directory must be writable by the account running the lab.
- **Incompatible database after editing schema:** stop the server, back up or move `database/lab.db`, and restart to reseed. Ordinary workshop use should use `/reset`.

## Contributing and publishing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and challenge design. GitHub Actions runs the regression suite on pushes and pull requests. See [SECURITY.md](SECURITY.md) for the distinction between intended exercises and unintended vulnerabilities.

Build a clean upload archive using only Python's standard library:

```bash
python scripts/package_release.py
```

The archive is written to `dist/ai-breachlab.zip`. It includes source, docs, tests, licenses, and GitHub templates; it excludes local state, environments, credentials, and the development brief. See the [GitHub publishing guide](docs/github-publishing.md) for upload steps. The repository runs a Flask backend; GitHub Pages cannot run the interactive lab.

## Author and license

Created by **GhostStag Security** as a contribution to practical AI security education.

Project code and documentation are available under the [MIT license](LICENSE). Bundled Bootstrap CSS retains its [upstream license](static/css/BOOTSTRAP-LICENSE.txt).
