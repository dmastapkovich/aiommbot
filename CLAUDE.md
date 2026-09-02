# CLAUDE.md

Guidance for AI coding agents working in this repository.

## Project state

`aiommbot` 0.5.0 is being **designed**, not implemented. There is no package code yet. The current
work is a wayfinder map (a GitHub issue labelled `wayfinder:map`) whose child issues are decision
tickets. Read the map first; it is the low-resolution view of everything decided so far.

Do not write library code until the map says implementation may start. Planning produces
decisions (ADRs, glossary terms, specifications), not deliverables.

## Standing preferences for this effort

- Inspirations: **django-modern-rest** for discipline and mechanically enforced quality;
  **FastStream** for agent-native repository layout and testing ergonomics.
- The quality bar is fixed and not up for re-negotiation per ticket: multiple strict type checkers,
  `ruff` with all rules, import-linter layer contracts, slots checking, full coverage, executable
  docs, typing tests, smoke imports without extras.
- Fresh start: no compatibility with `aiommbot 0.4.x`. Version starts at 0.5.0. MIT. English
  everywhere in the repository; the maintainer converses in Russian.
- Small core, explicit platform boundary, one Mattermost adapter. Minimise runtime dependencies.
  Every 0.4.x capability gets an explicit keep / redesign / drop decision.
- Async and sync APIs are both required, implemented without duplicated code paths.
- **Documentation is the product of this phase.** `docs/design/` is an arc42 architecture document
  with C4 diagrams in Mermaid; every component gets an LLD from `docs/design/components/_template.md`
  (patterns named as on refactoring.guru, explicit SOLID analysis, failure modes, typing/async rules,
  testing). `docs/design/engineering-style.md` is the rulebook every LLD and later every PR obeys.
  Read `docs/design/README.md` before touching the catalogue.

## Agent skills

### Issue tracker

Issues live in this repository's GitHub Issues (`gh` CLI). See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context: `CONTEXT.md` at the root and ADRs in `docs/adr/`. See `docs/agents/domain.md`.

### Research

Findings from primary sources are Markdown files in `docs/research/`, one per question, each
with a Sources section. New research goes there.

## Safety

- Never commit secrets or personal data. Never paste tokens, cookies or private URLs into issues.
- Commit and push only when the maintainer has approved it for the current effort.
