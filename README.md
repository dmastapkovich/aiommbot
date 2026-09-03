# aiommbot

> An async Python framework for building Mattermost bots, rewritten from scratch for 0.5.0:
> a small stateless core, an explicit platform boundary, quality enforced by mechanism, and a
> repository built to be developed together with AI coding agents.

**Status: design phase.** There is no code here yet, on purpose. Every hard-to-reverse decision is
being made in the open first — as a [wayfinder map](https://github.com/dmastapkovich/aiommbot/issues?q=label%3Awayfinder%3Amap)
of decision tickets, with the outcomes recorded in [`docs/adr/`](docs/adr/) and the vocabulary in
`CONTEXT.md`. Implementation starts only when the map is clear.

## Manifesto

- **A small core with an explicit platform boundary.** The core knows about events, routing,
  dependency injection and lifecycle. It does not know Mattermost; the Mattermost adapter does.
  Everything else — interactive webhooks, state, scheduling, observability — is a plugin that earns
  its place, and the boundary is enforced mechanically, not by convention.
- **Fault tolerance is the product.** A bot lives on a WebSocket for weeks. Reconnection, heartbeats,
  resume, backpressure and graceful drain are designed from primary sources and battle-tested
  clients, not bolted on later. See [`docs/research/`](docs/research/).
- **Quality by mechanism.** Multiple strict type checkers, `ruff` with everything on,
  import-linter contracts between layers, executable documentation, typing tests and full coverage.
  Nothing is enforced by "please remember".
- **Built with agents, owned by humans.** The repository ships the context an AI coding agent needs
  to contribute well — and a policy that keeps a human accountable for every merged line.
- **Async and sync, without copy-paste.** One implementation, two faces, using the current state of
  the art rather than parallel code paths.
- **Public from day one.** MIT licence, English everywhere, semantic versioning from 0.5.0.
  This is a clean successor to the internal `aiommbot 0.4.x`, with no compatibility layer.

## Lineage

`aiommbot 0.4.x` lives on in a private GitLab and is frozen. This repository starts a fresh public
history; ideas worth keeping from 0.4.x are re-decided here one ticket at a time.

## Licence

[MIT](LICENSE)
