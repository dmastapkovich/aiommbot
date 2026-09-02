# CLAUDE.md

Read `AGENTS.md` first — it is the canonical entry point and this file adds only what is specific
to Claude Code.

- Ask the maintainer through `AskUserQuestion`: at most four questions per round, the recommended
  option first and labelled `(Recommended)`, wording in Russian, one round at a time. Free-text
  answers are common — read them fully; they often reshape the question.
- Project skills are in `.claude/skills/` (symlinks into `.agents/skills/`). `design-session` is
  the one to run for any map ticket; `lld-author` for `LLD: <component>` tickets.
- Fact-finding is yours, not the maintainer's: dispatch a subagent for anything the filesystem,
  `gh`, or the web can answer, and keep only the decision for the human.
- Long research runs as background agents writing straight into `docs/research/`; commit each
  file as it lands and close its ticket with a resolution comment.
