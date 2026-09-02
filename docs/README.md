# Documentation catalogue

Everything written about aiommbot 0.5.0 lives under `docs/`, one directory per **document type**,
each with its own `README.md` index. Start here, pick the type, follow its index.

| Directory | Document type | Question it answers | Standard it follows |
|---|---|---|---|
| [`design/`](design/README.md) | Architecture document, component design documents, style rulebook, readiness tracker | How is the system built and why? | [arc42](https://arc42.org) + [C4](https://c4model.com) |
| [`adr/`](adr/README.md) | Architecture decision records | What did we decide, when, and what did we reject? | Nygard ADRs, one decision per file |
| [`research/`](research/README.md) | Research notes | What do primary sources say about a question? | Sources per claim, unverified marked |
| [`agents/`](agents/README.md) | Process documents for AI coding agents | How does a session work in this repository? | [writing-for-agents](agents/README.md) |
| `../CONTEXT.md` | Glossary | What do our words mean? | Ubiquitous language, one canonical term per concept |
| _(later)_ `tutorials/`, `how-to/`, `reference/`, `explanation/` | User documentation | How do I use the library? | [Diátaxis](https://diataxis.fr), decided by ticket #26 |

How documents are written, named, linked, reviewed and retired: [`documentation-style.md`](documentation-style.md).
What still has to be written: [`design/TRACKER.md`](design/TRACKER.md).
