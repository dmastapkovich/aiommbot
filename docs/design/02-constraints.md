# 2. Constraints

_Status: in progress (#37)._

## Technical constraints

- **Python `>=3.12`**, supported until each version's upstream EOL.
  → [ADR-0008](../adr/0008-python-floor-3-12-with-typing-extensions.md)
- **Core runtime dependencies: standard library + `typing_extensions`** only.
  → [ADR-0002](../adr/0002-core-scope-two-condition-test.md), [ADR-0008](../adr/0008-python-floor-3-12-with-typing-extensions.md)
- **Four blocking type checkers** beyond their strict presets. → [ADR-0009](../adr/0009-four-strict-type-checkers.md)
- **Zero suppressions in the package**; Quarantine modules for foreign types. → [ADR-0010](../adr/0010-zero-suppressions-with-a-quarantine.md)
- **One toolchain** for style, complexity, architecture and dependencies, `just` as the single entry
  point. → [ADR-0011](../adr/0011-lint-format-and-architecture-toolchain.md)
- **One distribution**, explicit composition, no compatibility promise toward any earlier release.
  → [ADR-0001](../adr/0001-fresh-start-as-a-public-package.md), [ADR-0002](../adr/0002-core-scope-two-condition-test.md)

## Organisational and convention constraints

Open-source quality from the first commit: MIT, English artefacts, semantic versioning from 0.5.0
([ADR-0001](../adr/0001-fresh-start-as-a-public-package.md)); documentation changes land in the same
commit as the decision. #37 completes the section.
