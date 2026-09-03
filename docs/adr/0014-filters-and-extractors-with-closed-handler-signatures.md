---
status: accepted
date: 2026-09-03
ticket: "#15"
---

# Filters are pure predicates, Extractors produce typed values, and handler signatures are closed

aiogram lets a filter return `bool | dict` and merges the dict into handler kwargs, so the type
checker cannot see which filter produced which parameter; its `MagicFilter` DSL is built on
dynamic attribute access, which ADR-0006 forbids. Every 0.4.8 handler needed `**kwargs: Any` to
survive middleware injection. We decided:

- **`Filter[P]` is a pure predicate** over `Event[P]`, composable with `&`, `|`, `~`
  (Strategy + Composite). Filters are explicit, typed classes and factories
  (`ChatType.DIRECT`, `Text.startswith("/")`); there is no dynamic DSL.
- **`Extractor[P, T]` parses an event into a typed value** the handler receives by annotation
  (`Command`, `RegexMatch`, `Submission[Model]`). It returns a typed result: `Value[T]`, or
  `NoMatch` (the event is not about this — the walk continues, as with a failed filter), or
  `Invalid` (the event is about this but the data is bad). `Invalid` skips the handler by
  default; a handler that annotates the parameter as `Submission[Model] | InvalidSubmission`
  receives the typed error and answers the user itself. Expected outcomes are values, never
  exceptions.
- **Closed handler signature.** The first parameter is `Event[P]`; every other parameter is
  resolved by its annotation — an extractor value or a dependency (mechanism in #16) — never by
  name. No `**kwargs`. A parameter nothing can provide is a start-up error (fail closed).
  Synchronous handlers are accepted and run in a thread pool (ADR-0004).
- Filters, extractors and their composition render as data for `HandlerSpec` (ADR-0013).

## Considered options

- *Filters returning `bool | typed object`* — rejected: one concept doing two jobs, and the
  parameter-to-producer link stays implicit.
- *Predicates plus a magic-filter DSL* — rejected: dynamic attribute access, no static checking.
- *Validation failures as exceptions in middleware* — rejected: the handler loses control of the
  user-facing answer (dialog field errors).
- *Open signatures with `**kwargs`* — rejected: they hide dependencies and defeat the checkers.
