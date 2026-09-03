# Architecture decision records

One decision per file, numbered in order of acceptance, never rewritten: a changed mind is a new
ADR that supersedes the old one. Format and triggers: [`_template.md`](_template.md). ADRs are
produced by wayfinder tickets; the map (#1) and `docs/design/TRACKER.md` §B list which ticket owns
which decision.

| ADR | Decision | Status |
|---|---|---|
| [0001](0001-fresh-start-as-a-public-package.md) | aiommbot 0.5.0 is a from-scratch public rewrite with no compatibility with 0.4.x | accepted |
| [0002](0002-core-scope-two-condition-test.md) | The core admits a capability only if every bot needs it identically or it is chat-specific with no library equivalent; stdlib-only core, one distribution, explicit composition | accepted |
| [0003](0003-stateless-core-state-plugin-with-explicit-backend.md) | The core is stateless; conversation state is a plugin that cannot start without an explicit backend | accepted |
| [0004](0004-async-engine-with-generated-sync-runtime.md) | One asyncio engine; the synchronous face is limited to the Runtime and generated from async | accepted |
| [0005](0005-one-ingress-many-workers.md) | A bot scales as one event ingress and many workers, never as identical replicas | accepted |
| [0006](0006-architectural-tenets-of-the-core.md) | The core is built by composition over Protocols it owns, with named patterns and strict typing | accepted |
| [0007](0007-tiny-public-root-with-explicit-subpackages.md) | The public API is a tiny root namespace plus explicit subpackages; everything else is internal | accepted |
| [0008](0008-python-floor-3-12-with-typing-extensions.md) | Python 3.12 is the floor, supported until EOL, with typing_extensions as the Core's only runtime dependency (amends 0002) | accepted |
| [0009](0009-four-strict-type-checkers.md) | Four type checkers run at maximum strictness and all of them block | accepted |
| [0010](0010-zero-suppressions-with-a-quarantine.md) | Zero lint and type suppressions in the package; foreign types wrapped in quarantine modules | accepted |
| [0011](0011-lint-format-and-architecture-toolchain.md) | One toolchain enforces style, complexity, architecture and dependencies; just is the entry point | accepted |
