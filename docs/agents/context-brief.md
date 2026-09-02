# Context brief

The warm-up for a new session. It compresses what earlier sessions learned and decided so the
conversation with the maintainer continues at the same altitude. Facts here are pointers, not
sources: the ADRs, the map and the research files are authoritative.

## The effort in one paragraph

`aiommbot` is an async Python framework for Mattermost bots. The internal 0.4.x line (~20k LOC,
eleven company bots, private GitLab) is frozen. 0.5.0 is a **from-scratch public rewrite** with a
clean history in this repository, MIT, English, starting at 0.5.0, with **no compatibility** with
0.4.x ([ADR-0001](../adr/0001-fresh-start-as-a-public-package.md)). The inspirations are
**django-modern-rest** (discipline, mechanically enforced quality, tiny public API, plugin isolation
via import-linter, executable docs, 100 % coverage) and **FastStream** (agent-native `.agents/skills`,
`_internal` boundary, in-memory `TestBroker`, `docs_src` with tests). This phase produces the design
catalogue; implementation is a later map.

## Settled while charting (do not reopen without new evidence)

- Destination: a complete design catalogue — glossary, ADRs, arc42 architecture document with HLD,
  a reviewed LLD per component, engineering style rulebook, standards, hand-off.
- Quality bar adopted whole from django-modern-rest: several strict type checkers (mypy, pyright,
  pyrefly, ty), `ruff` all rules, wemake-python-styleguide, import-linter contracts, slotscheck,
  100 % coverage, executable docs, typing tests, smoke imports without extras. Versions are a
  ticket; the level is not.
- Small core with an explicit platform boundary; only the Mattermost adapter is designed.
- Minimise runtime dependencies. Every 0.4.8 capability gets an explicit keep / redesign / drop.
  Scheduling, observability, CLI, reliability middlewares and durable storage backends are open
  questions of responsibility, not assumed features.
- Confirmed for 0.5.0: first-party testing toolkit, webhook interactive actions and dialogs, FSM.
- Async **and** sync APIs are required, produced without duplicated code paths.
- The WebSocket gateway must be top-tier fault tolerant, designed from primary sources.
- Documentation format: arc42 + C4 in Mermaid; LLD template with named patterns
  (refactoring.guru) and SOLID analysis; a separate engineering-style rulebook.
- No deadline; quality over speed. Many sessions are expected and accepted.

## Research digest (details and sources in `docs/research/`)

- **01 Mattermost WebSocket protocol.** Reliable websockets are always on; resume via
  `connection_id` + `sequence_number` with dead-queue replay (128), send queue 256, server ping
  60 s / pong wait 100 s; an unrecoverable gap yields a new connection and a fresh `hello`; a full
  send queue drops the connection. The TS client backs off 3 s → 300 s with 2 s jitter and pings
  every 30 s; the Go client never reconnects. `data.post` is a JSON string inside JSON. 110+ event
  names. An expired session leaves the socket open but silent.
- **02 Resilient WebSocket clients.** Every mature client combines application heartbeat with a
  dead-link deadline, full-jitter exponential backoff with a cap, resume-or-fresh-session, a
  close-code taxonomy, bounded receive queues with a stated overflow policy, graceful drain and
  consumer-side dedup. 18 numbered design rules with sources.
- **03 Bot framework architectures.** aiogram 3 is the routing/FSM reference (router propagation,
  filters returning data, outer/inner middleware, `StorageKey`, event isolation locks); discord.py
  has the strongest handler typing (`ParamSpec`/`Concatenate`); Bolt's name-based injection fails
  open; nobody ships FSM *and* a first-party testing toolkit — that is the gap. DI libraries
  compared: dishka, fast-depends, that-depends, wireup, linkd.
- **04 Modern Python library engineering (Sep 2026).** Python ≥ 3.13 recommended (3.15 final
  2026-10-01, 3.12 security-only); ty 0.0.77 pre-GA, pyrefly 1.0, mypy 2.3, ruff 0.16.5;
  uv_build + trusted publishing; msgspec on the hot path, pydantic at the edge; httpx stalled at
  0.28.1 for 21 months → aiohttp behind a Protocol; opentelemetry-api as a no-op core dependency;
  pluggy has no async hooks; mkdocs-material in maintenance mode.
- **05 Mattermost REST typing.** The spec covers bots completely but only 21/221 schemas declare
  `required`; `datamodel-code-generator` → msgspec passes mypy strict; recommended pipeline is
  pinned spec → overlay → generated models → one hand-written transport; WebSocket payload types
  come from the webapp's `websocket_messages.ts`.
- **06 Dual sync/async API.** Hand-written twins (httpx, websockets) cost hundreds of duplicated
  lines; code generation (httpcore, PyMongo's `synchro.py`) is the mature answer; runtime
  bridging costs ~50 µs per call; sync face only for the REST client; greenlet rejected.
- **07 Durable bot state.** Redis + in-memory are the universal first-party pair; MongoDB is a
  later community add-on wherever it exists; no precedent for one "storage profile" binding
  state, locks and idempotency; recommend a minimal storage Protocol, a separate locking
  protocol and a shipped conformance suite.
- **08 Peer responsibility boundaries.** No peer bot framework owns scheduling, metrics, retries,
  DLQ, breakers or Sentry in core; python-telegram-bot demoted JobQueue to an extra; FastStream
  removed built-in retry as a mistake; Litestar owns rate limiting and paid with a CVE.
  Bot-specific keepers: FSM isolation, callback signing, stale-action dedup, flood control.
- **09 Usage mining of the eleven 0.4.x bots.** 8 of 13 event kinds unused; reliability
  vocabulary and built-in breaker 0/11; testing toolkit 2/11; the default error middleware
  swallows exceptions and leaks PII in 8/11; two storage-configuration styles coexist; core
  candidates are message/action/dialog handlers, `direct_added`, FSM, answer/update,
  attachments, lifespan + `bot.state`.
- **10 Plugin systems.** Django: explicit registration, three-stage boot forbidding import-time
  side effects, checks framework, per-app settings objects. Litestar/FastStream: explicit plugin
  list with narrow protocols and friendly missing-dependency errors. Sanic-Ext's
  "installed ⇒ active" is the anti-pattern. Candidate: `Bot(plugins=[...])`, narrow `Plugin`
  Protocol, declare/act split, typed per-plugin settings, entry points only for third-party
  discovery, import-linter isolation, shipped contract tests.

## The 0.4.8 codebase, for reference

Local copy at `/Users/dsastapkovich/workspace/bo_cloud_ru/backoffice-portal/mattermost-bots/aiommbot`
with the eleven bots beside it. Known debts: `Bot(Router)` god object with eight concerns,
thirteen parallel request classes and per-type dispatchers, ~555 `Any`, 58 `noqa`, deferred
imports in eight files as a circular-import workaround, 2,158 lines of bespoke webhook
cryptography, hand-maintained docs that drifted from the code. Worth keeping as *ideas*: one
observability seam with a no-op default, storage profiles, the testing toolkit, per-event-type
backpressure policies, DI resolved once at registration, friendly "install extra" errors.

## How the maintainer works

- Speaks Russian; wants the repository in English. Answers questions in rounds and often in free
  text that reshapes the question — read the whole answer.
- Wants **ideology before features**: what the bare core does, how functionality is enabled, how
  contributors add plugins. Django's app model is the reference they asked to react to.
- Allergic to copy-paste and to pulling in libraries "just because"; asks whether a capability is
  the bot framework's responsibility at all before designing it.
- Values the state of the art over habit: expects primary-source facts, named patterns, SOLID
  reasoning and current (2026) tooling, and says so when a proposal feels dated.
- Likes concrete artefacts to react to (code sketches, diagrams) and wants a FastStream-docs-style
  handler catalogue eventually (issue #34) — keep handlers introspectable as data.
- Prefers recommendations stated first with the reason, then the alternatives.
