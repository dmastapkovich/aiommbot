# Documentation-engineering notes

Findings gathered from primary sources about **how this catalogue is written** — what the arc42
template requires of a section, what a diagram renderer can carry — as opposed to what the product
does. They live here because `docs/` holds only the project (`AGENTS.md`, *Standing rules*): the
audience of a note here is the author of a document rather than its reader.

Each file answers one question, carries a source per claim, marks what it could not verify and ends
with a Sources section — the form of [`docs/research/README.md`](../../docs/research/README.md),
which indexes the product notes. The numbering is one sequence across both directories, so a number
identifies a note wherever it lives and is never reused.

**A note is never the thing an agent obeys.** A rule a note produced lives in a rulebook — the
diagram conventions, the quality checklist, the `hld-author` skill — and the rule links the note
once as its provenance. Read a note to change a rule, not to follow one.

| File | Question |
|------|----------|
| [`37-arc42-runtime-view.md`](37-arc42-runtime-view.md) | What does arc42 require of a runtime view (§6), and how do published arc42 documents keep one? |
| [`38-mermaid-sequence-diagram-limits.md`](38-mermaid-sequence-diagram-limits.md) | Which constructs does a Mermaid sequence diagram support, which are unreliable on the renderers this catalogue is read through, and what limits follow? |
