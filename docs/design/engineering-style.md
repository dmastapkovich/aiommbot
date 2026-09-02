# Engineering style and ideology

_Status: not started (owning ticket: Engineering style and ideology)._

The rules every component document and, later, every pull request must follow. Planned contents:

- **Ideology.** Small core, explicit boundaries, quality by mechanism, design before code, built
  with agents and owned by humans.
- **SOLID in Python.** What each principle means for this codebase with concrete do/don't examples:
  single responsibility per module and class; extension through Protocols and plugins rather than
  modification; substitutability of adapters and storages; narrow, client-specific Protocols; core
  depends on abstractions it owns, never on adapters or optional libraries.
- **Pattern catalogue.** Patterns from [refactoring.guru](https://refactoring.guru/design-patterns)
  that are welcome here and where (e.g. Strategy for filters, Chain of Responsibility for
  middleware, Observer/Mediator for the event bus, Builder for message composition, Adapter for the
  platform, Facade for the public API, State for FSM, Template Method vs. composition), patterns
  that are banned or discouraged and why (Singleton, service locators, god objects, deep
  inheritance), and the refactoring smells reviewers look for.
- **Language rules.** Typing (PEP 695 generics, `Protocol`, `TypeIs`, `Final`, `@override`,
  `__slots__`, no `Any`/`cast`/`getattr`), async rules (structured concurrency, cancellation
  safety, timeouts everywhere, no blocking calls, no fire-and-forget tasks), error handling
  (typed error taxonomy, no swallowed exceptions), naming, module layout, public vs. `_internal`.
- **Documentation rules.** Docstrings, doc examples that execute, ADR triggers, comment style
  (the why, two lines, cite the issue).
- **Review checklist** derived from all of the above.
