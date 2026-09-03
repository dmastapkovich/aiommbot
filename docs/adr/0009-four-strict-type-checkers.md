---
status: accepted
date: 2026-09-03
ticket: "#23"
---

# Four type checkers run at maximum strictness and all of them block

The typing specification has one conformance suite but several implementations that still
disagree; each checker also has blind spots the others cover. We decided to run **mypy, pyright,
pyrefly and ty** in CI, **each configured beyond its `strict` preset**, and **each blocking**:

- **mypy**: `strict = true`, `extra_checks`, and the optional error codes `exhaustive-match`,
  `redundant-self`, `unimported-reveal`, `possibly-undefined`, `truthy-bool`, `truthy-iterable`,
  `ignore-without-code`, `explicit-override`, `mutable-override`, `deprecated`, `redundant-expr`,
  `unused-awaitable`, `narrowed-type-not-subtype`, `warn_unused_ignores`.
- **pyright**: `strict` on the package plus `reportUnnecessaryTypeIgnoreComment`,
  `reportImplicitOverride`, `reportShadowedImports`, `reportImportCycles`,
  `reportUninitializedInstanceVariable`, `reportPropertyTypeMismatch`, `reportUnusedCallResult`,
  `reportMissingSuperCall`, `reportImplicitStringConcatenation`; `--verifytypes aiommbot` at
  **100 %** completeness; `py.typed` shipped.
- **pyrefly**: `strict` preset.
- **ty**: `[tool.ty.rules] all = "error"`, the opt-in `unsound-*` rules, strict literal and
  generic narrowing, `respect-type-ignore-comments = false`.

Every rule switched off anywhere carries a one-line reason in `pyproject.toml`. Checker versions
are pinned exactly in the dev dependency group and bumped in dedicated commits, because ty and
pyrefly move weekly and do not follow semantic versioning.

**Typing tests** live in `tests/typing/*.py`: ordinary modules with `typing.assert_type`, checked
by all four checkers and never imported by pytest. Negative cases ("this must not type-check")
are written as a targeted suppression with a rule code on the offending line; when the error
disappears, the "unnecessary suppression" report of each checker turns the line red.

## Considered options

- *ty as source of truth + pyright, mypy dropped* — rejected by the maintainer: the bar is
  maximum coverage of specification divergences, and the cost of a fourth checker is CI minutes,
  not design.
- *Presets only* — rejected: the optional rules (explicit override, unused awaitable, import
  cycles, unused call results) catch exactly the defects an async framework produces.
