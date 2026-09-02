# Contributing

> **Draft.** The project is in its design phase; this document will be finalised by the wayfinder
> tickets on tooling, CI and release process. What is written here already applies.

## Where the work happens right now

Design decisions are made as GitHub issues labelled `wayfinder:*`. The issue labelled
`wayfinder:map` is the index; its child issues are the open questions. The outcome of every closed
question lives in [`docs/adr/`](docs/adr/) (decisions) and `CONTEXT.md` (vocabulary). Read those
before proposing a change — an argument that is already settled there needs new evidence to reopen.

## Ground rules

- Code, comments, tests, docs, commit messages and issues are written in English.
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`,
  `docs:`, `refactor:`, `test:`, `chore:`), with an optional scope.
- Every change that touches behaviour comes with tests and, when it changes the public surface,
  with documentation.
- Quality gates are mechanical and non-negotiable. Do not weaken a linter, type checker or coverage
  threshold to make a change pass; fix the design instead.
- See [`.github/AI_POLICY.md`](.github/AI_POLICY.md) for how AI tooling may and may not be used.

## Security

Please report vulnerabilities privately as described in [`SECURITY.md`](SECURITY.md).
