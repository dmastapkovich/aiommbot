# Research notes

Findings gathered from primary sources (official docs, source code, RFCs) for the 0.5.0 design.
Each file answers one question, carries a source per claim, marks what it could not verify and ends
with a Sources section. Notes are inputs to decisions, not decisions: where an ADR decided
otherwise, the note points at the ADR (`docs/documentation-style.md` §8, §9).

| File | Question |
|------|----------|
| [`01-mattermost-websocket-protocol.md`](01-mattermost-websocket-protocol.md) | What must a fault-tolerant Mattermost WebSocket client know and do? |
| [`02-resilient-websocket-client-patterns.md`](02-resilient-websocket-client-patterns.md) | What do battle-tested real-time clients (Slack, Discord, NATS, websockets, aiohttp) do for reconnect, heartbeat, backpressure? |
| [`03-bot-framework-architectures.md`](03-bot-framework-architectures.md) | How do aiogram 3, discord.py, hikari, Bolt, PTB structure API, routing, DI, FSM, middleware, testing, typing? |
| [`04-modern-python-library-engineering-2026.md`](04-modern-python-library-engineering-2026.md) | What is the state of the art (Sep 2026) for a strictly typed async OSS Python library developed with AI agents? |
| [`05-mattermost-rest-typing-codegen.md`](05-mattermost-rest-typing-codegen.md) | Can the typed Mattermost REST layer be generated from the OpenAPI spec, and with which tool? |
| [`06-dual-sync-async-api.md`](06-dual-sync-async-api.md) | How do libraries offer sync and async APIs from one implementation, and what should we do? |
| [`07-durable-bot-state-storage.md`](07-durable-bot-state-storage.md) | How do bot frameworks persist conversation state; is MongoDB common; what is the minimal storage contract? |
| [`08-peer-responsibility-boundaries.md`](08-peer-responsibility-boundaries.md) | Scheduling, observability, CLI, reliability: core, plugin, recipe or absent in peer frameworks? |
| [`10-plugin-systems.md`](10-plugin-systems.md) | What plugin models (Django apps, pluggy, entry points, Litestar, FastStream, Sphinx, Home Assistant) teach us? |
| [`11-webhook-ingress-patterns.md`](11-webhook-ingress-patterns.md) | How do peer frameworks bring HTTP callbacks into an event-driven core, and what does Mattermost's callback contract actually look like? |
| [`12-error-boundary-conventions.md`](12-error-boundary-conventions.md) | What do frameworks and task systems do by default when a handler raises, who owns the decision, and should the Core have a boundary? |
| [`13-conversation-state-lifetime.md`](13-conversation-state-lifetime.md) | How do bot frameworks and stateless designs bound the lifetime of per-conversation state? |
| [`14-websocket-client-libraries.md`](14-websocket-client-libraries.md) | Which WebSocket client library sits behind the `WebSocketConnection` Protocol, and which HTTP client for REST? |
| [`15-mattermost-session-revocation.md`](15-mattermost-session-revocation.md) | What does the Mattermost server do to an open WebSocket when the session is revoked or expires, and how does a client detect it? |
| [`16-webhook-callback-standards.md`](16-webhook-callback-standards.md) | What do standards (RFC 9421, Standard Webhooks, RFC 8725, PASETO) and Mattermost itself say about callback reply timing, authenticity and replay protection? |
| [`17-http-client-observability.md`](17-http-client-observability.md) | What observer surface, record fields and logging policy should the outbound Mattermost REST client expose, and how does it stay OpenTelemetry-compatible without depending on it? |
| [`18-execution-model-in-practice.md`](18-execution-model-in-practice.md) | Do reference frameworks accept synchronous callables and how, how do they expose dual faces, and what does async→sync tooling cost? |
| [`19-provided-and-required-protocol-inventories.md`](19-provided-and-required-protocol-inventories.md) | Is a Protocol the framework hands to user code the same kind of thing as one it calls out through, and does an inventory of such Protocols mark the difference? |
| [`20-reply-slot-variance-and-capability-typing.md`](20-reply-slot-variance-and-capability-typing.md) | How should the generic envelope `Event[P, R]` carry a typed Reply channel so that assignability holds under all four type checkers, and where does the `ReplyAlreadySent` marker live? |
| [`21-measured-facts-behind-the-rules.md`](21-measured-facts-behind-the-rules.md) | What does the strictly typed peer that the rulebook and ADRs 0006, 0007, 0031, 0033 and 0034 cite actually contain, measured fact by fact with a source per claim? |
| [`22-public-import-surface-of-modern-libraries.md`](22-public-import-surface-of-modern-libraries.md) | How do modern strictly typed libraries lay out the public import surface across root and subpackages, which layouts stay extensible, and what did changing one cost? |
| [`23-dispatch-observability-in-async-frameworks.md`](23-dispatch-observability-in-async-frameworks.md) | How does a framework offer observability of its dispatch path without imposing a dependency, through which mechanism and under which names, and how does the application decline it? |
| [`24-library-logging-design.md`](24-library-logging-design.md) | What logger tree, level policy, correlation mechanism and structured path can a zero-dependency async library ship, and what does a log call cost? |
| [`25-cli-entry-points-and-what-clis-configure.md`](25-cli-entry-points-and-what-clis-configure.md) | What does the packaging machinery guarantee about a console script behind an optional dependency, what do peer CLIs contain and configure, and what does an argument parser cost? |
| [`26-schedule-reliability-and-probe-primitives.md`](26-schedule-reliability-and-probe-primitives.md) | What cron, retry, rate-limiting and circuit-breaking primitives exist in Python, what do peers ship for scheduling and why, and what contract must a health probe satisfy? |
| [`27-application-contributed-readiness-checks.md`](27-application-contributed-readiness-checks.md) | When a framework ships liveness and readiness endpoints, in what shape does an application contribute its own checks, and what runs them? |
| [`28-arc42-deployment-view-and-cross-cutting-concepts.md`](28-arc42-deployment-view-and-cross-cutting-concepts.md) | What do arc42 §7 and §8 require, and what is left as §8's own content once a project keeps a decision log? |
| [`30-plugin-contract-versioning.md`](30-plugin-contract-versioning.md) | How does a plugin host version the contract it offers plugins, separately from its own release version, and what happens where it does not? |
| [`31-error-tracker-integration-anatomy.md`](31-error-tracker-integration-anatomy.md) | What does a first-party error-tracker integration do that `capture_exception` does not, and what does the SDK already do with no framework integration at all? |
| [`32-plugin-lifecycle-failure.md`](32-plugin-lifecycle-failure.md) | What does a host do when a plugin fails to start or fails to stop, and what do `AsyncExitStack` and `asyncio.TaskGroup` guarantee about it? |
| [`33-the-plugin-to-plugin-channel.md`](33-the-plugin-to-plugin-channel.md) | Through which sanctioned channel does one plugin reach another plugin's capability, keyed on what, and is the channel typed? |
| [`34-plugin-conflicts-and-prohibitions.md`](34-plugin-conflicts-and-prohibitions.md) | Which conflicting declarations does a plugin host refuse, at what moment and with what message, and what does it state a plugin may not do? |
| [`35-the-third-party-author-kit.md`](35-the-third-party-author-kit.md) | What does a host hand a third-party plugin author besides the Protocol definitions — a contract kit, a scaffold, a name convention, a logger name, a promise about field names? |
