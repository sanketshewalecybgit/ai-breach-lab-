# Security policy

AI BreachLab is an intentionally vulnerable educational application. Run it on localhost or an isolated training environment with fictional data. Publishing the source on GitHub does not require exposing a running lab to the internet.

## Intended behavior

Vulnerable mode deliberately demonstrates object authorization failures, excessive agency, invalid business actions, sensitive context exposure, indirect prompt injection, and unsafe tool chains. The challenge definitions and instructor answer key describe these exercises. They are expected behavior in vulnerable mode.

## Unintended issues

Bypasses of secure mode, remote code execution, unexpected network access, CSRF/host-validation bypasses, unsafe rendering, and exposure of real host files are outside the intended exercises. Dependency and deployment issues are also relevant.

Use the repository's **Security → Report a vulnerability** option if the maintainer has enabled private reporting. If that option is unavailable, open a minimal issue requesting a private contact channel without posting exploit details or sensitive data. There is no promised response time or paid bounty program.

Include the affected revision, mode, fictional demo identity, expected behavior, minimal reproduction, and impact. Test only your own isolated copy. Do not provide real credentials or customer data.

## Maintainer preparation

Before publishing, enable GitHub private vulnerability reporting if available. The current source tree is the maintained version; there is no support commitment for older snapshots. Review dependency updates against both the vulnerable exercises and the defensive regression tests.
