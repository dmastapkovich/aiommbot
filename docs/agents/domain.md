# Domain documents

How `CONTEXT.md` and `docs/adr/` are consumed and maintained by every session.

## Before working

Read `CONTEXT.md` at the repository root, then the ADRs that touch the area of the ticket
(`docs/adr/README.md` lists them by decision). Both exist; a session never creates them from
scratch.

## Use the glossary's vocabulary

When your output names a domain concept — in an issue title, a proposal, a diagram, a test name —
use the term as `CONTEXT.md` defines it. Never drift to a synonym the glossary lists under
`_Avoid_`. If the concept you need has no term, that is a gap: propose the term to the maintainer
and add it in the same commit as the document that needs it.

## Flag ADR conflicts

If your output contradicts an accepted ADR, say so explicitly rather than silently overriding:

> _Contradicts ADR-0003 (stateless Core) — worth reopening because…_

The maintainer decides. If the decision changes, the ADR is rewritten in the same commit and the
new ADR and the rewritten one link each other (`amends` / `amended-by`).

## `CONTEXT.md` format

```md
# aiommbot

{One or two sentences: what this context is and why it exists.}

## Language

**Term**:
{One or two sentences defining what it IS, not what it does.}
_Avoid_: synonym, synonym
```

Be opinionated: one canonical term per concept, the rejected synonyms under `_Avoid_`. Only terms
specific to this project belong; general programming concepts do not. `CONTEXT.md` is a glossary
and nothing else — no implementation detail, no specification — and it never uses a word from its
own `_Avoid_` lists.

## ADR format

`docs/adr/_template.md`. Number = highest existing + 1; a retired number is not reused. Add the row
to `docs/adr/README.md` and to `docs/design/TRACKER.md` §B in the same commit.
