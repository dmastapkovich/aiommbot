# Design catalogue

This directory is the **solution design** of aiommbot 0.5.0: the architecture document, one design
document per component, the engineering style, and the diagram conventions. It is written before
the code and is the source the implementation is checked against.

The catalogue follows **[arc42](https://arc42.org/overview)** for the architecture document and the
**[C4 model](https://c4model.com/)** for diagrams, rendered as Mermaid inside Markdown so every
diagram renders on GitHub, is reviewed in pull requests and is diffed like code.

## Map of the catalogue

| arc42 section | File | Owning ticket(s) |
|---|---|---|
| 1. Introduction and goals | [`01-introduction-and-goals.md`](01-introduction-and-goals.md) | Solution design: goals, constraints, quality scenarios |
| 2. Constraints | [`02-constraints.md`](02-constraints.md) | same |
| 3. Context and scope | [`03-context-and-scope.md`](03-context-and-scope.md) | HLD: context, containers and components |
| 4. Solution strategy | [`04-solution-strategy.md`](04-solution-strategy.md) | Core ideology; Plugin model; HLD |
| 5. Building block view | [`05-building-block-view.md`](05-building-block-view.md) | HLD: context, containers and components |
| 6. Runtime view | [`06-runtime-view.md`](06-runtime-view.md) | HLD: runtime views |
| 7. Deployment view | [`07-deployment-view.md`](07-deployment-view.md) | HLD: deployment and cross-cutting concepts |
| 8. Cross-cutting concepts | [`08-cross-cutting-concepts.md`](08-cross-cutting-concepts.md) | same, plus the boundary tickets |
| 9. Architecture decisions | [`../adr/`](../adr/) | every grilling ticket |
| 10. Quality requirements | [`10-quality-requirements.md`](10-quality-requirements.md) | Solution design: goals, constraints, quality scenarios |
| 11. Risks and technical debt | [`11-risks-and-technical-debt.md`](11-risks-and-technical-debt.md) | Solution design: risk register |
| 12. Glossary | [`../../CONTEXT.md`](../../CONTEXT.md) | maintained inline by every ticket |
| Engineering style and ideology | [`engineering-style.md`](engineering-style.md) | Engineering style and ideology |
| Diagram conventions | [`diagrams.md`](diagrams.md) | Documentation foundation (this task) |
| Component design documents (LLD) | [`components/`](components/) | one `LLD: <component>` ticket each |

Each file starts with a status line: `Status: not started | in progress (#ticket) | reviewed`.

## How the catalogue grows

1. A wayfinder grilling ticket resolves a decision → an ADR is written and the relevant arc42
   section is updated in the same commit.
2. When the building-block view is settled, every component listed there gets its own
   `LLD: <component>` ticket and a file in `components/` created from
   [`components/_template.md`](components/_template.md).
3. A component document is *reviewed* only when every section of the template is filled, its
   diagrams agree with the building-block and runtime views, and it links to the ADRs it depends on.
4. The hand-off ticket checks the whole catalogue for contradictions before implementation starts.

## Rules

- **Design before code.** No implementation module exists without a reviewed component document.
- **One truth per fact.** A decision lives in its ADR; the catalogue links to it and never restates
  it. Vocabulary lives in `CONTEXT.md`; the catalogue uses those terms and no synonyms.
- **Patterns are named.** When a component applies a design pattern, name it as
  [refactoring.guru](https://refactoring.guru/design-patterns/catalog) does and say *why* it is
  the right fit here and which alternative was rejected.
- **SOLID is checked, not assumed.** Every component document has a SOLID section that argues each
  principle for that component or says honestly where it is bent and why.
- **Diagrams are code.** Mermaid only, following [`diagrams.md`](diagrams.md). No screenshots, no
  binary diagram files.
