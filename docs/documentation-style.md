# Documentation style

The standard every document in this repository follows, so the catalogue can grow for years without
losing its shape. Documentation is treated as code: it lives in the repository, changes in the same
commit as what it describes, is reviewed against a checklist, and is linted in CI.

## 1. Document types and where they live

Every document has exactly one **type**, and every type has exactly one home directory with an
index (`README.md`). A new document goes into an existing type or the type is added to
[`README.md`](README.md) first — never a stray file.

| Type | Home | One document is… | Template |
|---|---|---|---|
| Architecture section | `design/NN-*.md` | one arc42 section | stub with status line |
| Component design document (LLD) | `design/components/<term>.md` | one component | `design/components/_template.md` |
| Rulebook | `design/engineering-style.md`, `design/diagrams.md` | one set of rules for one activity | — |
| Readiness tracker | `design/TRACKER.md` | the single status view | — |
| Decision record | `adr/NNNN-<slug>.md` | one decision | `adr/_template.md` |
| Research note | `research/NN-<slug>.md` | one question answered from primary sources | see `research/README.md` |
| Agent process document | `agents/*.md` | one process question | `writing-for-agents` conventions |
| Glossary | `CONTEXT.md` (root) | the ubiquitous language | format in `agents/domain.md` |
| User documentation | `tutorials/ how-to/ reference/ explanation/` (later) | one Diátaxis quadrant each | decided by ticket #26 |

## 2. One document, one question

A document answers one question stated in its first paragraph. If a second question appears, it
becomes a second document and a link. This is what makes the catalogue extensible: adding knowledge
means adding a file and an index row, never growing a file until it covers everything.

## 3. Front matter and status

Every document under `design/` and `adr/` opens with a status line or YAML front matter:

```text
_Status: not started | in progress (#N) | reviewed | superseded by <link>._
```

ADRs use YAML (`status`, `date`, optional `supersedes`/`superseded-by`). `reviewed` is granted only
by [`agents/design-quality-checklist.md`](agents/design-quality-checklist.md); the status is
mirrored in [`design/TRACKER.md`](design/TRACKER.md) in the same commit.

## 4. Naming

- Files and directories: kebab-case, English. Numeric prefixes only where order carries meaning
  (arc42 sections `01-`…`11-`, ADRs `0001-`…, research notes `01-`…).
- Component documents are named after the `CONTEXT.md` term, nothing else.
- ADR titles state the decision, not the topic: *"Sync API is generated from the async
  implementation"*, not *"Sync/async"*.
- Headings are sentence case. Section numbering inside a document only where a template defines it.

## 5. Vocabulary

Use `CONTEXT.md` terms exactly; the glossary lists the synonyms to avoid. A concept without a term
is a gap to resolve in the glossary first, in the same commit. Diagrams use the same words as prose.

## 6. Linking

- Relative links, always to a file and, where helpful, an anchor. No bare URLs in prose; link text
  names the target.
- Link **down** the hierarchy for detail (section → component document → ADR) and **up** for
  context (component document → building-block view). Never restate what the link target says:
  a decision lives in its ADR, a fact in its research note, a term in the glossary.
- Every index (`README.md`) lists every document in its directory. An unindexed document does not
  exist.

## 7. Diagrams

Mermaid only, following [`design/diagrams.md`](design/diagrams.md): C4 levels for structure,
sequence diagrams for behaviour with failure branches, state diagrams for stateful nodes. One
diagram answers one question; names match the glossary.

## 8. Writing

English. Active voice, present tense. Short sentences; one idea each. Concrete over abstract:
name the component, the constant, the source. Say *why* next to *what*. Quote constants and
version numbers from primary sources with a link; mark anything unverified as such. Prefer a table
when three or more things are compared on the same attributes. No marketing language.

## 9. Change discipline

- A document changes in the same commit as the decision, code or research that changes it, with a
  Conventional Commit message and the issue number.
- Never delete history: an outdated ADR is `superseded by`, an outdated section is rewritten and
  the ADR that changed it is linked. The map, the tracker and the ADR index carry the trail.
- Review = the checklist. A document is `reviewed` when every applicable line is true, not when
  someone feels done.

## 10. Discovering something the design did not foresee

While researching, grilling or writing an LLD, a capability, detail or mechanism may surface that
no ticket, section or ADR anticipates. Do not design it in passing and do not drop it. Run the
**discovery protocol** in [`agents/session-playbook.md`](agents/session-playbook.md#discovery-protocol):
classify it (out of scope · fog · sharp question · backlog idea · gap in this document type),
record it where that class lives, link it from the current ticket, and continue the current ticket
unchanged. The map stays the single register of what is still open; the tracker stays the single
register of what is done.

## 11. Tooling (docs as code)

Enabled by the docs-linting task and finalised by ticket #26: Markdown lint, prose lint with a
project vocabulary (Vale), dead-link check (lychee), Mermaid syntax check, and a check that every
file in a typed directory appears in its index. Until then the checklist is the lint.

## References

arc42 (arc42.org) · C4 model (c4model.com) · Diátaxis (diataxis.fr) · Nygard, *Documenting
Architecture Decisions* · Google developer documentation style guide · Write the Docs, *Docs as
Code* · django-modern-rest and FastStream documentation as living precedents.
