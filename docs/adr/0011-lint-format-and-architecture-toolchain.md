---
status: accepted
date: 2026-09-03
ticket: "#23"
---

# One toolchain enforces style, complexity, architecture and dependencies; `just` is the single entry point

Quality is enforced by mechanism (ADR-0006). We fixed the mechanisms and the way they are run:

- **ruff** with `select = ["ALL"]` and `preview = true`, blocking. Every ignored rule is listed in
  `pyproject.toml` with a reason. Known ignores from day one: the `TC` family (it pushes imports
  into `TYPE_CHECKING` blocks, which we forbid), `D203`/`D213` and `COM812` (conflict with the
  formatter). `flake8-tidy-imports` `banned-api` forbids `typing.cast`, `typing.TYPE_CHECKING`
  and `typing.Any` outside annotations; `ANN401` forbids `Any` in annotations.
- **ruff format**: line length 100, double quotes, Google docstring convention; docstrings
  required for public names (`D1xx` off for `_internal` and tests); Markdown code blocks are
  formatted too.
- **wemake-python-styleguide 1.x** as a blocking gate (`flake8 --select=WPS`) with tight limits
  on arguments, complexity, nesting, module members and imports: the mechanical guard against
  god objects and long signatures.
- **semgrep** with repository rules in `.semgrep/` for what ruff cannot express — dynamic
  `getattr`/`hasattr`/`setattr`, `Any` in expressions, bare `type: ignore`, direct
  `__annotations__` access, mutable module globals — each rule with a "do this instead" message
  and covered by `semgrep --test`; plus the public `p/python` and `p/security-audit` rule sets.
- **import-linter** contracts in `pyproject.toml`: `layers` (core → adapter → plugins direction
  of allowed imports), `forbidden` (optional libraries importable only from their plugin or
  quarantine module), `independence` (plugins do not import each other).
- **slotscheck** with `require-subclass` and `require-superclass`; data classes are
  `@dataclass(slots=True, frozen=True, kw_only=True)`, service classes declare `__slots__`;
  Protocols and listed ABCs are the exceptions.
- **deptry**, `uv lock --check` and `uv audit` keep extras honest, the lock current and
  dependencies free of known vulnerabilities; **typos** for spelling; **pyproject-fmt** for a
  canonical `pyproject.toml`; **zizmor** for GitHub Actions hygiene.
- **`just`** is the single entry point for people, agents and CI (`just` with no arguments lists
  the recipes); **pre-commit** runs the fast recipes locally (ruff, checkers on changed files,
  typos, pyproject-fmt, Conventional Commits, secret scan) and CI runs everything on the whole
  tree.

## Considered options

- *ruff 0.16 defaults + `extend-select`* — rejected: new rule families would not switch on by
  themselves; `ALL` with explained ignores keeps the default maximal.
- *Complexity metrics via ruff only (`PLR09xx`, `C901`)* — rejected: WPS adds module-level
  metrics (members, imports, Jones complexity) that ruff lacks; its flake8 host is slow but the
  package is small.
- *A bespoke AST linter instead of semgrep* — rejected: our own linter is code to test and
  maintain; semgrep rules are declarative, versioned and self-tested.
- *Makefile* — rejected: file-target semantics and `.PHONY` noise for what is a command runner.
