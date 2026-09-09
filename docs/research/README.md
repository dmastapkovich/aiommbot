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
