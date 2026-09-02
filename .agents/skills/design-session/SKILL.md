---
name: design-session
description: Use when working any ticket of the aiommbot 0.5.0 wayfinder map (issue #1) — research, grilling, prototype, LLD or task — or when the maintainer says "take the next ticket", "продолжим карту", or names an issue number.
---

# Design session

Run one map ticket end to end. The steps and their completion criteria are in
`docs/agents/session-playbook.md`; this skill is the order in which to load context and the
guardrails that keep sessions identical in shape.

1. Warm up exactly as `AGENTS.md` lists: `docs/agents/context-brief.md`, then `gh issue view 1`,
   then `docs/design/TRACKER.md`, then the ticket and its closed blockers' resolution comments.
2. Choose the ticket: the one the maintainer named, else the first open sub-issue of #1 with no
   open blocker and no assignee (`issue_dependencies_summary.blocked_by == 0`). Claim it.
3. Follow the playbook section for the ticket's `wayfinder:*` label.
4. Before closing, walk `docs/agents/design-quality-checklist.md` for every touched document.
5. Close, update the map and the tracker, report in Russian, stop. One ticket per session.

Guardrails: decisions are the maintainer's, facts are yours; questions go through
`AskUserQuestion` in rounds of at most four with the recommendation first; every choice lands in
an ADR or a glossary term the moment it is made; documents only — no package code on this map.
