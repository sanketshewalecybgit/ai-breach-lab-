# Security policy

AI BreachLab is an intentionally vulnerable educational application. Run it on localhost or an isolated training environment with fictional data. Publishing the source on GitHub does not require exposing a running lab to the internet.

## Intended behavior

Vulnerable mode deliberately demonstrates object authorization failures, excessive agency, invalid business actions, sensitive context exposure, indirect prompt injection, unsafe tool chains, and virtual URL-fetching SSRF. The challenge definitions and instructor answer key describe these exercises. They are expected behavior in vulnerable mode.

Expert additionally simulates reference poisoning, persistent destination-memory contamination, cross-company document retrieval, changed/replayed/expired approval execution, and tool-description manipulation. The customer/review outboxes are local database records. Reference and integration editors can only alter fictional text. Each demo identity’s Expert case and evidence remain isolated by the server; bypassing that isolation through the workspace routes is not an intended challenge.

The RAG Poisoning upload form accepts bounded UTF-8 `.txt`/`.md` references into the current identity’s case. Uploaded text is stored in SQLite, escaped when displayed, and searchable by the simulated assistant. Client filenames never determine filesystem paths. Ingestion does not execute instructions; retrieved directives use the same fixed capabilities and secure provenance checks as seeded references. Uploads cannot select their company or classification, and fresh-case/full-lab resets clear the corresponding uploaded references.

The assistant URL fetcher resolves only fixed virtual fixtures, including a
fictional public-to-internal redirect. Both modes reject arbitrary destinations;
secure mode also restricts every destination to the public HTTPS origin. Actual
network access, DNS resolution and host-file reads are outside this exercise.

## Unintended issues

Bypasses of secure mode, remote code execution, unexpected network access, CSRF/host-validation bypasses, unsafe rendering, and exposure of real host files are outside the intended exercises. Dependency and deployment issues are also relevant.

Use the repository's **Security → Report a vulnerability** option if the maintainer has enabled private reporting. If that option is unavailable, open a minimal issue requesting a private contact channel without posting exploit details or sensitive data. There is no promised response time or paid bounty program.

Include the affected revision, mode, fictional demo identity, expected behavior, minimal reproduction, and impact. Test only your own isolated copy. Do not provide real credentials or customer data.

## Maintainer preparation

Before publishing, enable GitHub private vulnerability reporting if available. The current source tree is the maintained version; there is no support commitment for older snapshots. Review dependency updates against both the vulnerable exercises and the defensive regression tests.
