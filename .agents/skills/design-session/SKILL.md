---
name: design-session
description: "Use when working any ticket of the aiommbot 0.5.0 wayfinder map (GitHub issue 1) — research, grilling, prototype, LLD or task — or when the maintainer says take the next ticket, продолжим карту, or names an issue number."
---

# Design session

Run one map ticket end to end. The steps and their completion criteria are in
`docs/agents/session-playbook.md`; this skill is the order in which to load context and the
guardrails that keep sessions identical in shape.

1. Warm up in the order `AGENTS.md` lists, ending with the ticket and the resolution comments of
   its closed blockers.
2. Choose the ticket: the one the maintainer named, else the first open sub-issue of #1 with no
   open blocker and no assignee (`issue_dependencies_summary.blocked_by == 0`). Claim it through
   `gh api` (`docs/agents/issue-tracker.md`, *Writes*).
3. Resolve per the playbook section for the ticket's `wayfinder:*` label. For `wayfinder:lld` the
   *Resolve* step is the `lld-author` skill.
4. Verify every touched document against `docs/agents/design-quality-checklist.md`; then record in
   one commit and push; then close, update the map, clear the fog, report in Russian, stop. One
   ticket per session.

Guardrails: decisions are the maintainer's, facts are yours; questions go through
`AskUserQuestion` in rounds of at most four with the recommendation first; every choice lands in
an ADR or a glossary term the moment it is made; documents state only the target design and use
the glossary exactly; documents only — no package code on this map.
