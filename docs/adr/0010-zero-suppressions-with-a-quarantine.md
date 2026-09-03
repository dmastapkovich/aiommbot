---
status: accepted
date: 2026-09-03
ticket: "#23"
---

# The package carries zero lint and type suppressions; foreign types are wrapped in quarantine modules

A suppression comment is a recorded concession: it says the code does not meet the rule and
somebody decided to live with it. Two exemplary libraries we measured still carry them in bulk
(one holds 100 `type: ignore` and 252 `noqa` in 191 files, another 144 `type: ignore` in 509),
almost all at the boundary with third-party libraries whose annotations are incomplete. We are
designing before writing, so we decided the stricter rule that is achievable when it is set from
the first line:

- **No suppressions in `aiommbot/`**: no `noqa`, no `type: ignore`, no `pyright:`/`ty:`/
  `pyrefly: ignore`, no `per-file-ignores` for package paths. Code that a rule rejects is
  redesigned, not annotated.
- **Quarantine is the single exception.** Third-party libraries with incomplete typing
  (aiohttp, msgspec, redis, …) are wrapped in dedicated modules under `_internal/compat/`, each
  adapting one library to a Core-owned Protocol. Only there may a suppression appear, always
  with a rule code and a link to the upstream issue. A test counts quarantine suppressions
  against a committed baseline that may only decrease; raising it is a separate commit with a
  written reason.
- **Tests and documentation examples** may relax rules by directory (`S101` asserts, private
  access, docstrings), listed once in `pyproject.toml` with reasons; they may not carry inline
  suppressions either.
- **Unused suppressions are errors** everywhere (`RUF100`, `warn_unused_ignores`,
  `reportUnnecessaryTypeIgnoreComment`, ty's equivalent), which is also what makes the negative
  typing tests of ADR-0009 work.

## Considered options

- *Absolute zero, no quarantine* — rejected: it makes CI hostage to upstream typing gaps and to
  bugs in four fast-moving checkers, and pushes the concession into local `.pyi` stubs that are
  themselves unchecked code.
- *Targeted suppressions anywhere with a budget* — rejected by the maintainer: any suppression in
  our own code is technical debt, and a project designed from scratch starts with none.
