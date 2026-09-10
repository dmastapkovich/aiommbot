# Issue tracker: GitHub

Tickets live as GitHub issues in this repository; the map is issue #1. Reads use the `gh issue`
commands; **every write goes through `gh api`**, one command per call, with multi-line bodies
drafted into a file first.

## Reads

- One ticket with its comments: `gh issue view <n> --comments`.
- The open frontier: `gh issue list --state open --json number,title,labels,assignees`.
- The map: `gh issue view 1`.

## Writes

`<owner>/<repo>` is `dmastapkovich/aiommbot`. `<db-id>` is an issue's numeric database id
(`gh api repos/<owner>/<repo>/issues/<n> --jq .id`), not its `#number`.

| Action | Command |
|---|---|
| Create a ticket | `gh api repos/<owner>/<repo>/issues -f title="…" -F body=@body.md -f 'labels[]=wayfinder:<type>'` |
| Make it a child of the map | `gh api --method POST repos/<owner>/<repo>/issues/1/sub_issues -F sub_issue_id=<db-id>` |
| Detach a resolved ticket from the map | `gh api --method DELETE repos/<owner>/<repo>/issues/1/sub_issue -F sub_issue_id=<db-id>` |
| Block it on another ticket | `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>` |
| Claim | `gh api --method PATCH repos/<owner>/<repo>/issues/<n> -f 'assignees[]=<login>'` |
| Comment | `gh api --method POST repos/<owner>/<repo>/issues/<n>/comments -F body=@comment.md` |
| Close | `gh api --method PATCH repos/<owner>/<repo>/issues/<n> -f state=closed -f state_reason=completed` |
| Edit the map body | `gh api --method PATCH repos/<owner>/<repo>/issues/1 -F body=@map.md` |

## Wayfinding vocabulary

- **Map**: the single issue labelled `wayfinder:map`, holding Destination, Notes, Decisions so far,
  Not yet specified and Out of scope. GitHub caps a parent at **100 sub-issues** and counts closed
  ones, so the map keeps only the open ones: the *Close* step detaches the ticket it just closed,
  whose record is then its line under *Decisions so far* plus the `Part of #1` line in its own body.
  A batch of detachments is one `gh api graphql` call over aliased `removeSubIssue` mutations —
  `gh` inside a shell loop does not run here.
- **Ticket**: a sub-issue of the map with one `wayfinder:<type>` label — `research`, `grilling`,
  `prototype`, `task` or `lld`. An `lld` ticket is titled `LLD: <component>`, one per component of
  §5.10 of the building-block view; it writes `docs/design/components/<term>.md` and its
  `blocked_by` edges are the writing order of
  [ADR-0035](../docs/adr/0035-lld-order-is-a-topological-sort-of-structural-contract-dependencies.md),
  from which the *Wave* column of `docs/design/components/README.md` is derived.
- **Blocking**: GitHub's native issue dependencies. `issue_dependencies_summary.blocked_by` counts
  open blockers; a ticket is unblocked when it is zero.
- **Frontier**: the open sub-issues of the map with no open blocker and no assignee, in map order.
- **Claim**: the assignee. An open, unassigned ticket is unclaimed; the claim is the session's first
  write.
- **Resolve**: a `## Resolution` comment, then close, then the map line under *Decisions so far*,
  then detach the ticket from the map.
