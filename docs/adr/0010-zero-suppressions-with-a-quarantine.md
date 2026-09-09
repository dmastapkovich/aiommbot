---
status: accepted
date: 2026-09-03
ticket: "#23"
---

# The package carries zero lint and type suppressions; foreign types are wrapped in quarantine modules

A suppression comment is a recorded concession: it says the code does not meet the rule and somebody
decided to live with it. Even an exemplary library carries them in bulk — django-modern-rest holds
100 `type: ignore` ([`docs/research/21`](../research/21-measured-facts-behind-the-rules.md)) —
almost all at the boundary with third-party code whose annotations are incomplete. We are designing
before writing, so we decided the stricter rule that is achievable when it is set from the first
line:

- **No suppressions in `aiommbot/`**: no `noqa`, no `type: ignore`, no `pyright:`/`ty:`/
  `pyrefly: ignore`, no `per-file-ignores` for package paths. Code that a rule rejects is
  redesigned, not annotated.
- **Quarantine is the single exception.** Third-party libraries with incomplete typing (httpx2,
  websockets, msgspec, redis, …) are wrapped in dedicated modules under the `_internal/compat/` of
  the rank that owns the library
  ([ADR-0040](0040-one-package-directory-per-import-rank.md)), each adapting one library to a
  Core-owned Protocol. Only there may a suppression appear, always with a
  rule code and a link to the upstream issue. A test counts quarantine suppressions against a
  committed baseline that may only decrease; raising it is a separate commit with a written reason.
- **Tests and documentation examples** may relax rules by directory (`S101` asserts, private
  access, docstrings), listed once in `pyproject.toml` with reasons; they may not carry inline
  suppressions either.
- **Unused suppressions are errors** everywhere (`RUF100`, `warn_unused_ignores`,
  `reportUnnecessaryTypeIgnoreComment`, ty's equivalent), which is also what makes the negative
  typing tests of [ADR-0009](0009-four-strict-type-checkers.md) work.

## Considered options

- *Absolute zero, no quarantine* — rejected: it makes CI hostage to upstream typing gaps and to
  bugs in four fast-moving checkers, and pushes the concession into local `.pyi` stubs that are
  themselves unchecked code.
- *Targeted suppressions anywhere with a budget* — rejected by the maintainer: any suppression in
  our own code is technical debt, and a project designed from scratch starts with none.

## `tests/typing/` is the second named exception

A negative typing case ("this must not type-check") *is* a targeted suppression with a rule code
on the offending line ([ADR-0009](0009-four-strict-type-checkers.md)), and it works only because
every checker reports an unnecessary suppression as an error. `tests/typing/` is therefore the
**second named exception** alongside Quarantine, under three conditions:

- only a suppression that carries the rule code, and only as the assertion of a negative case —
  never to make a positive case pass;
- **no baseline**: unlike Quarantine, the count is not tracked, because such a suppression is not a
  concession but the subject of the test, and it is *required* to turn red the day the checker stops
  reporting the error;
- the directory is checked by all four checkers and never imported by pytest
  ([ADR-0009](0009-four-strict-type-checkers.md)), so a suppression here cannot mask anything at
  runtime.

Everywhere else: `aiommbot/` carries none, Quarantine's carry a rule code and an
upstream link against a baseline that only decreases, and tests and documentation examples relax
rules by directory in `pyproject.toml` with reasons rather than inline.
