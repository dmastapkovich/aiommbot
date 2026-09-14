---
status: accepted
date: 2026-09-14
ticket: "#103"
amends: [ADR-0007, ADR-0015, ADR-0043]
---

# A field of a public frozen dataclass is a public name, listed on the reference page and guarded both ways

[ADR-0015](0015-plugin-contract-and-composition.md) promised that field names stay stable, "so one
setting has one name", about names that satisfy none of
[ADR-0007](0007-tiny-public-root-with-explicit-subpackages.md)'s four criteria: a `dataclass` field
has no leading underscore and lives in a public module, but it is not a name re-exported `X as X`
and [ADR-0043](0043-explicit-re-export-with-a-reference-page-as-the-public-list.md)'s guard test
compares importable names, which a field is not. Renaming `Health(cache_ttl=…)` in a patch release
was therefore formally permitted and obviously wrong — and since
[ADR-0070](0070-plugins-do-not-collaborate-the-composition-hands-one-instance-to-both.md) the field
is also the name of a wiring point rather than only of a value.

- **The field travels with its type, so criterion 3 is satisfied by the type's own re-export.** The
  four checkers of [ADR-0009](0009-four-strict-type-checkers.md) already treat a keyword-only
  dataclass's field names as part of its contract: a consumer who misspells one fails type checking
  today. This decision makes the promise match what the checkers already enforce, rather than adding
  a fifth criterion beside the four.
- **The reference page carries the field list under the type's row**, and it is hand-written for the
  same reason the rest of the page is — criterion 4 stays a decision somebody made on purpose
  (ADR-0043). Generating it, as litestar and opentelemetry do, removes the drift and removes the
  decision with it
  ([`docs/research/44`](../research/44-keeping-a-documented-field-list-in-step-with-the-code.md)).
- **The guard test reads the page and `dataclasses.fields()` in both directions and names both**,
  which is **CPython's** shape: it scrapes one machine-parsable entry per name out of its own prose,
  takes the symmetric difference, and exits reporting *Undocumented* and *Documented nonexistent* as
  separate sets. It is the existing ADR-0043 test reading one more column of the same table, not a
  second mechanism. **celery's lesson comes with it**: its `configcheck` builder does exactly this
  for 207 settings, carries an ignore list, and has never failed a pull request because CI does not
  select it — so this test runs in the same required job as the rest.
- **The per-field prose lives beside the field**, as a Google `Attributes:` block in the class
  docstring. That is what django-modern-rest does for `OpenAPIConfig`, its own frozen, slotted,
  keyword-only public configuration object — the same shape as ours — and what stamina does. The
  page carries the names; the class carries the explanation.
- **A rename is a breaking change and there is no alias.** The only frozen-dataclass rename in the
  corpus shipped as one: litestar's `DTOConfig.field_mapping` became `rename_fields`, tagged
  `:breaking:`, with `TypeError: unexpected keyword argument` for the old call. Every alias
  precedent — celery's `Option.old`, django's per-name branch, pytest's second option name —
  belongs to a dictionary configuration, where the old key is data and can be mapped. A frozen
  keyword-only dataclass has no such seam, and inventing one would mean a hand-written `__init__` in
  every settings type. The window over the change is **#28**'s.
- **The promise does not reach a third-party Plugin's own fields.** No host in the survey says
  anything about them ([`docs/research/35`](../research/35-the-third-party-author-kit.md)); Home
  Assistant comes closest only because a custom integration's keys are user-facing YAML. The
  plugin-API section of the reference page
  ([ADR-0080](0080-the-plugin-api-is-a-section-of-the-reference-page.md)) tells an author that this
  is the rule we keep for ours, and promises nothing on their behalf.

## Considered options

- *Make the name importable instead, django-modern-rest's answer* — rejected as inapplicable: its
  settings are a mapping whose keys are members of a public `StrEnum`, so each key is an ordinary
  public name and satisfies all four criteria by construction. Ours are keyword arguments of a
  frozen dataclass, and a keyword argument cannot be made importable without giving up the typed
  object that ADR-0015 chose.
- *A fifth rule covering settings types only* — rejected: two mechanisms of publicity free to
  disagree, and it leaves `ProcessProfile`, `EventMeta`, the Request record and `PluginSpec` outside
  a promise their field names equally carry.
- *Generate the page from the code* — rejected above: it is the one shape that cannot drift, and it
  makes a name public by existing, which is what ADR-0007's fourth criterion exists to prevent.
- *An import-time `assert` binding the field set, django-modern-rest's mechanism* — rejected as
  insufficient rather than wrong: it binds code to code, `python -O` strips it, and the page stays
  outside the loop, which is the drift this decision is about.

## Consequences

- Every public frozen dataclass is covered, not only a Plugin's settings: `ProcessProfile`,
  `EventMeta`, the Request record, the Stats snapshot and `PluginSpec` have field names under the
  same promise, which is why the rule is stated about the shape rather than about settings.
- The reference page's rows grow a field list, which is a change to its shape and therefore to
  ADR-0043; the audience column of ADR-0080 is the other.
- `ST-MOD-01` and `ST-MOD-11` state the public-surface rules and now have a field-shaped case; the
  rulebook says so where it defines the surface.
