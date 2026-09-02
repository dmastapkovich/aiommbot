# Security Policy

> **Draft**, to be completed when the first release is cut.

## Reporting a vulnerability

Please do **not** open a public issue for security problems. Use GitHub's private vulnerability
reporting on this repository ("Security" → "Report a vulnerability"). You will get an
acknowledgement within a few days and a plan for the fix and disclosure.

## Scope

Anything in this repository that ships in the `aiommbot` package. Bots built on top of it are out
of scope unless the problem is caused by the framework.

## Practices we commit to

- Minimal runtime dependencies; optional integrations are extras.
- Dependency and workflow auditing in CI.
- Releases published to PyPI through trusted publishing, without long-lived tokens.
- No secrets, tokens or personal data in logs, labels or error messages by design.
