---
status: accepted
date: 2026-09-09
ticket: "#24"
---

# A public name is a redundant-alias re-export listed on a hand-written reference page, and the package carries no `__all__`

[ADR-0007](0007-tiny-public-root-with-explicit-subpackages.md) made a name public only when it is
explicitly re-exported *and* documented, and left the mechanism open. We decided the two mechanisms
that realise those criteria:

- **The re-export is the redundant alias** — `from .router import Router as Router`,
  `import codec as codec`, or `from . import codec`. The typing specification treats exactly these
  forms as re-exports and every other imported symbol as private
  ([*Distributing type information*](https://typing.python.org/en/latest/spec/distributing.html)),
  which is what makes the four checkers of
  [ADR-0009](0009-four-strict-type-checkers.md) and a consumer's checker agree about our surface.
  `pyright --verifytypes` then measures completeness over that set
  ([pyright, *Typed libraries*](https://microsoft.github.io/pyright/#/typed-libraries)).
- **The list is a hand-written reference page**, one public name per row and machine-readable, and a
  guard test compares it with what actually imports **in both directions**: a name on the page that
  does not import fails, and an importable name missing from the page fails. That is what keeps
  ADR-0007's fourth criterion a decision somebody made on purpose instead of a by-product of the
  code. Which path a row names is
  [ADR-0042](0042-a-public-name-is-documented-at-its-package-path.md)'s; the page's renderer is
  #26's; that it is written by hand and parsable is this decision's.

**The package carries no `__all__`.** It would be a second list of the same names beside the first,
and the drift has a direction: once a module has an `__all__`, that list overrides every other rule,
so a name re-exported `X as X` and forgotten in the list is silently private for consumers
([`docs/research/22`](../research/22-public-import-surface-of-modern-libraries.md) §5.1). The
completeness the list would buy — pyright's `reportUnsupportedDunderAll`, pyrefly's
`bad-dunder-all`, ruff's `F822` under preview — is what the guard test already checks, and it checks
it against the documentation rather than against the module. The library we measure against carries
no `__all__` anywhere and re-exports sixteen names with the alias form
([`docs/research/21`](../research/21-measured-facts-behind-the-rules.md)). The form needs no lint
relaxation either: `PLC0414` does not apply in an `__init__.py`, which is the only place we
re-export (`docs/research/22` §5.5).

**The internal API gets its own page**, and its first line says that nothing on it is public and
that all of it may change in a patch release. It exists because a contributor or an agent reading
our code needs the shape of `_internal` explained somewhere other than the source, and the same
library documents its internals for exactly that reason (`docs/research/21`). A page that promises
nothing is safe to write; a page nobody wrote is read as "there is nothing here".

## Considered options

- *`__all__` in every public module as the canonical list, with the page generated from it* —
  rejected: it gives one machine-readable artefact and a diff to review, but a name then becomes
  documented by being added to a tuple, and criterion 4 stops being a separate human decision.
- *Both `__all__` and the alias form* — rejected above: three tools instead of one test, in
  exchange for a second list per `__init__.py` whose omissions are silent.
- *A committed text fixture as the list, with the page generated from the fixture* — rejected: it
  is the same generation with one more file; the page is already a file we control.
