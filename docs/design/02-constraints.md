# 2. Constraints

_Status: in progress (#23 settled the technical constraints below; #37 completes the section)._

## Technical constraints

- **Python `>=3.12`**, supported until each version's upstream EOL; CI matrix 3.12–3.15 plus a
  blocking free-threaded 3.14t job; annotations read lazily (PEP 649-safe).
  → [ADR-0008](../adr/0008-python-floor-3-12-with-typing-extensions.md)
- **Core runtime dependencies: standard library + `typing_extensions`** only; everything else lives
  in the Adapter or in Plugins behind Core-owned Protocols, enforced by import-linter.
  → [ADR-0002](../adr/0002-core-scope-two-condition-test.md), [ADR-0008](../adr/0008-python-floor-3-12-with-typing-extensions.md)
- **Four blocking type checkers** (mypy, pyright, pyrefly, ty) beyond their strict presets;
  `py.typed`; 100 % type completeness. → [ADR-0009](../adr/0009-four-strict-type-checkers.md)
- **Zero suppressions in the package**; quarantine modules for foreign types with a
  decreasing-only baseline. → [ADR-0010](../adr/0010-zero-suppressions-with-a-quarantine.md)
- **Toolchain**: ruff `ALL` + preview, WPS, semgrep, import-linter, slotscheck, deptry, uv audit,
  typos, pyproject-fmt, zizmor; `just` + pre-commit.
  → [ADR-0011](../adr/0011-lint-format-and-architecture-toolchain.md)
- **One distribution**, explicit composition, no compatibility with 0.4.x.
  → [ADR-0001](../adr/0001-fresh-start-as-a-public-package.md), [ADR-0002](../adr/0002-core-scope-two-condition-test.md)

## Organisational and convention constraints

Open-source quality from the first commit: MIT, English artefacts, Conventional Commits, semantic
versioning from 0.5.0, documentation changes in the same commit as the decision. Detailed in #37.
