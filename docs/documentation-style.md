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
| Agent process document | `agents/*.md` | one process question | — |
| Glossary | `CONTEXT.md` (root) | the ubiquitous language | format in `agents/domain.md` |
| User documentation | `tutorials/ how-to/ reference/ explanation/` (later) | one Diátaxis quadrant each | decided by ticket #26 |

Prototypes and sketches made while resolving a ticket are attached to the ticket; they are never
committed.

## 2. One document, one question

A document answers one question stated in its first paragraph. If a second question appears, it
becomes a second document and a link. This is what makes the catalogue extensible: adding knowledge
means adding a file and an index row, never growing a file until it covers everything. An ADR
records one decision; two decisions that could be revisited independently are two ADRs.

## 3. Status

Every arc42 section, component design document and rulebook under `design/` opens with exactly
one of these lines and nothing else on it:

```text
_Status: not started (#N)._
_Status: in progress (#N)._
_Status: reviewed (#N)._
```

`#N` is the ticket that owns the document; for a reviewed document it is the ticket that granted
the status. Indexes, the tracker and templates carry no status line.

ADRs use YAML front matter: `status: proposed | accepted`, `date`, `ticket`, and the optional
`amends` and `amended-by` lists that link an ADR to the ADRs that changed it or that it changed. A
decision withdrawn in full retires its file; the ADR index keeps the number with a pointer to the
ADRs that replaced it.

`reviewed` is granted only by [`agents/design-quality-checklist.md`](agents/design-quality-checklist.md)
and mirrored in [`design/TRACKER.md`](design/TRACKER.md) in the same commit.

## 4. Naming

- Files and directories: kebab-case, English. Numeric prefixes only where order carries meaning
  (arc42 sections `01-`…`11-`, ADRs `0001-`…, research notes `01-`…). A retired number is not
  reused.
- Component documents are named after the `CONTEXT.md` term, nothing else.
- ADR titles state the decision, not the topic: *"The Core runs on standard-library asyncio"*, not
  *"Async runtime"*.
- Headings are sentence case. Section numbering inside a document only where a template defines it.

## 5. Vocabulary

Use `CONTEXT.md` terms exactly; the glossary lists the synonyms to avoid, and the glossary itself
uses no word from its own `_Avoid_` lists. A concept without a term is a gap to resolve in the
glossary first, in the same commit. Diagrams use the same words as prose. A vocabulary correction
is made in place wherever the old word stands — in an ADR title as much as in a paragraph — because
the words are not the decision.

## 6. Linking

- Relative links, always to a file and, where helpful, an anchor. No bare URLs in prose; link text
  names the target. An `ADR-NNNN` or `docs/research/NN` mention is a link, never a code span.
- Link **down** the hierarchy for detail (section → component document → ADR) and **up** for
  context (component document → building-block view). Never restate what the link target says:
  a decision lives in its ADR, a fact in its research note, a term in the glossary. An arc42 section
  or the tracker may summarise a decision in one sentence next to its link.
- Every index (`README.md`) lists every document in its directory. An unindexed document does not
  exist. A planned document may have an index row before its file exists; the row names the file
  in a code span and links only once the file is committed.

## 7. Diagrams

Mermaid only, following [`design/diagrams.md`](design/diagrams.md): C4 levels for structure,
sequence diagrams for behaviour with failure branches, state diagrams for stateful nodes. One
diagram answers one question; names match the glossary.

## 8. Writing

English. Active voice, present tense. Short sentences; one idea each. Concrete over abstract:
name the component, the constant, the source. Say *why* next to *what*. Quote constants and
version numbers from primary sources with a link; mark anything unverified as such. Prefer a table
when three or more things are compared on the same attributes. No marketing language.

## 9. Target state only

A document describes the design as it is decided now, and nothing else. This is a rule of the
catalogue, not a design decision: the design is what the ADRs say; this section says how the
catalogue says it.

- A decision that changes an earlier document **rewrites** that document in the same commit, so it
  states the current decision; the ADR that caused the change is linked (`amended-by`), and the
  change is otherwise invisible in the text. No "amended by", "superseded", "previously" or "was"
  narrative anywhere.
- Nothing refers to a predecessor code base, an internal deployment, an internal repository or
  bot, a local path, or compatibility with anything outside this repository. Evidence from such
  sources may inform a session; it is never written down. Arguments rest on principle, primary
  sources and public peers cited as evidence in `research/`.
- A ticket reference points at open work (`decided by #N`). When the ticket closes, the sentence
  is rewritten to state the decision and link its ADR.
- Every document changes in the same commit as the decision or research that changes it, with a
  Conventional Commit message of the form `docs(<area>): <what was decided> (#N)`.
- Review = the checklist. A document is `reviewed` when every applicable line is true, not when
  someone feels done.

The commit history is the record of what a document used to say.

## 10. Discovering something the design did not foresee

While researching, grilling or writing an LLD, a capability, detail or mechanism may surface that
no ticket, section or ADR anticipates. Do not design it in passing and do not drop it. Run the
**discovery protocol** in [`agents/session-playbook.md`](agents/session-playbook.md#discovery-protocol):
classify it (out of scope · fog · sharp question · backlog idea · gap in this document type),
record it where that class lives, link it from the current ticket, and continue the current ticket
unchanged. The map stays the single register of what is still open; the tracker stays the single
register of what is done.

## 11. Tooling (docs as code)

Enabled by #43 and finalised by #26: Markdown lint, prose lint with a project vocabulary (Vale),
dead-link check (lychee), Mermaid syntax check, and a check that every file in a typed directory
appears in its index. Until then the checklist is the lint.

## References

[arc42](https://arc42.org) · [C4 model](https://c4model.com) · [Diátaxis](https://diataxis.fr) ·
Nygard, *Documenting Architecture Decisions* · Google developer documentation style guide · Write
the Docs, *Docs as Code*.
