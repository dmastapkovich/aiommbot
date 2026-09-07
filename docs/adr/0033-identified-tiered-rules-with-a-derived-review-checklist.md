---
status: accepted
date: 2026-09-07
ticket: "#36"
---

# A style rule is an identified, tiered statement carrying a reason, an example and its limits, and the review checklist is derived from the rules and nothing else

[ADR-0006](0006-architectural-tenets-of-the-core.md) fixed the tenets and sent them to this ticket
to become rules; [ADR-0011](0011-lint-format-and-architecture-toolchain.md) fixed the tools and
asked for a human-readable list of banned patterns to write semgrep rules against. A rulebook that
27 component design documents and later every pull request must obey is only usable if a rule can be
*cited* rather than paraphrased, and only honest if a reader can tell a rule that already blocks CI
from a rule that lives on a reviewer's attention. We decided the shape of
[`docs/design/engineering-style.md`](../design/engineering-style.md):

- **Every rule has a stable identifier** `ST-<AREA>-NN` over ten areas — `SOL`, `PAT`, `TYP`,
  `ASY`, `ERR`, `NAM`, `MOD`, `LOG`, `DOC`, `TST`. Identifiers are never renumbered and never
  reused: a retired rule keeps its number and is marked withdrawn. A semgrep rule written for
  ADR-0011 takes the identifier of the rule it enforces, so the linter message and the rulebook
  cannot drift apart.
- **Every rule carries seven parts**: the identifier; the rule stated positively as an imperative
  sentence; a one-line reason; at least one do/don't example; **limitations** — when the rule does
  not apply, or the explicit words *no exceptions*; the enforcement tier; where it is checked; and
  the ADR or research note it comes from. The limitations slot is what stops a rule from being
  cargo-culted into a place it was never meant for, and its absence is what makes a *banned* rule
  read as an opinion.
- **Two enforcement tiers.** `tool` — a linter, a type checker, a contract or a test already
  rejects the violation, and the rule exists to explain it. `review` — nothing mechanical can
  decide it. Only the tier is named in the rulebook, plus the semgrep identifier where it equals
  the rule's own; the tool configuration itself stays in ADR-0011, which remains the single place
  where a tool is chosen.
- **Three tiers for a pattern.** *Welcome* — argued once in the catalogue, so a component document
  cites the entry and names the place instead of re-arguing it. *Restricted* — permitted only with
  an ADR that names the rejected alternative. *Banned* — no exception, and every banned entry says
  what enforces it.
- **The review checklist at the end is derived from the rules above it and from nothing else**, in
  two blocks. *Design review* lists every rule tagged `LLD`, whatever its tier, because at design
  time no tool has run. *Code review* lists only `review`-tier rules, because re-checking by hand
  what CI already blocks is how a checklist stops being read. Every checklist line names the
  identifiers it covers, so the derivation is visible rather than asserted.
- **The rulebook is the single source for the rules it owns.** The component-design lines of
  [`design-quality-checklist.md`](../agents/design-quality-checklist.md) that used to restate
  typing, async and testing requirements now delegate to it. Where the rulebook meets a neighbour,
  the rule is the rulebook's line and the realisation is the neighbour's: package paths, `__all__`
  and extras are #24's; the testing toolkit's shape is #25's; the documentation stack is #26's; the
  observability boundary and the observer record are #29's; the ruff, WPS, semgrep and
  import-linter configuration is ADR-0011's.

Evidence that the shape works: the reference implementation we measured keeps its rules as an
agent-facing document of about 1,570 lines in exactly this template — imperative heading, one-line
reason, `Wrong:`/`Correct:` pair, `Limitations:`, deep link — and keeps no prose styleguide,
architecture document or ADR set at all, expressing its architecture as commented `import-linter`
contracts instead.

## Considered options

- *Headings only, cited by section number* — rejected: a citation from 27 component documents
  breaks the moment a section is inserted, and semgrep rules would need names of their own.
- *Identifiers without an enforcement tier* — rejected: it removes any risk of drifting from
  ADR-0011, but a reviewer then cannot tell which rules are already red in CI, and the checklist
  cannot be short.
- *One checklist over all rules* — rejected: complete, but it spends a reviewer's attention on
  what a linter decided better, and such checklists stop being read.
- *An advisory pattern catalogue* — rejected: it would put the whole weight back on each
  component document's pattern paragraph, which is the duplication the catalogue exists to remove.

## Consequences

- The rulebook and ADR-0011 must be changed together when a `tool`-tier rule's enforcement moves;
  the tier column is the seam between them and the only place they overlap.
- Prototype ticket #32, which verifies the toolchain on a stub, gains the banned-pattern list as
  its semgrep input, and owns the explained ignores `ASYNC109` and `RUF029`.
- A rule with no example is an unfinished rule, not a terse one: the checklist of
  `design-quality-checklist.md` already refuses the document without it.
