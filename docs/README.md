# Documentation catalogue

Everything written about aiommbot 0.5.0 lives under `docs/`, one directory per **document type**,
each with its own `README.md` index. Start here, pick the type, follow its index.

| Directory | Document type | Question it answers | Standard it follows |
|---|---|---|---|
| [`design/`](design/README.md) | Architecture document, style rulebook, diagram conventions, readiness tracker | How is the system built and why? | [arc42](https://arc42.org) + [C4](https://c4model.com) |
| [`design/components/`](design/components/README.md) | Component design documents (LLD) | How is one component built, and why that way? | `design/components/_template.md` |
| [`adr/`](adr/README.md) | Architecture decision records | What did we decide and what did we reject? | Nygard ADRs, one decision per file |
| [`research/`](research/README.md) | Research notes | What do primary sources say about a question? | Sources per claim, unverified marked |
| [`../CONTEXT.md`](../CONTEXT.md) | Glossary | What do our words mean? | Ubiquitous language, one canonical term per concept |
| _(later)_ `tutorials/`, `how-to/`, `reference/`, `explanation/` | User documentation | How do I use the library? | [Diátaxis](https://diataxis.fr), decided by ticket #26 |

How documents are written, named, linked, reviewed and kept to the target state:
[`documentation-style.md`](documentation-style.md). What still has to be written:
[`design/TRACKER.md`](design/TRACKER.md).
