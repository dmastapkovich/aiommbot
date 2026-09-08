# CLAUDE.md

Read `AGENTS.md` first — it is the canonical entry point and this file adds only what is specific
to Claude Code.

- Ask the maintainer through `AskUserQuestion`, following the rounds rule of
  `.agents/session-playbook.md` (at most four questions, recommended option first and labelled
  `(Recommended)`, wording in Russian, one round at a time). Free-text answers are common — read
  them fully; they often reshape the question.
- Project skills are in `.claude/skills/` (symlinks into `.agents/skills/`). `design-session` runs
  every map ticket; for an `LLD: <component>` ticket it hands the *Resolve* step to `lld-author`.
- Fact-finding is yours, not the maintainer's: dispatch a subagent for anything the filesystem,
  `gh`, or the web can answer, and keep only the decision for the human.
- Long research runs as background agents writing straight into `docs/research/`; finish each per
  the playbook's *Research ticket* step 2.
- GitHub writes use `gh api` (issue writes through `gh issue …` are sandboxed here); one command
  per Bash call, bodies drafted into files first. If `gh api` or `git push` is blocked, hand the
  maintainer the exact commands instead of retrying.
- Documents state only the target design (`AGENTS.md`, *Standing rules*). When you find junk,
  legacy or a stale sentence, fix it in the same commit — do not annotate it.
