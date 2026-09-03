# Research notes

Findings gathered from primary sources (official docs, source code, RFCs) for the 0.5.0 design.
Each file answers one question and ends with a Sources section. They are inputs to decisions, not
decisions — see `docs/adr/` for what was actually decided.

| File | Question |
|------|----------|
| `01-mattermost-websocket-protocol.md` | What must a fault-tolerant Mattermost WebSocket client know and do? |
| `02-resilient-websocket-client-patterns.md` | What do battle-tested real-time clients (Slack, Discord, NATS, websockets, aiohttp) do for reconnect, heartbeat, backpressure? |
| `03-bot-framework-architectures.md` | How do aiogram 3, discord.py, hikari, Bolt, PTB structure API, routing, DI, FSM, middleware, testing, typing? |
| `04-modern-python-library-engineering-2026.md` | State of the art for a strictly typed async OSS Python library developed with AI agents (Sep 2026). |
| `05-mattermost-rest-typing-codegen.md` | Can the typed Mattermost REST layer be generated from the OpenAPI spec, and with which tool? |
| `06-dual-sync-async-api.md` | How do libraries offer sync and async APIs from one implementation, and what should we do? |
| `07-durable-bot-state-storage.md` | How do bot frameworks persist conversation state; is MongoDB common; what is the minimal storage contract? |
| `08-peer-responsibility-boundaries.md` | Scheduling, observability, CLI, reliability: core, plugin, recipe or absent in peer frameworks? |
| `09-usage-mining-0.4.x-bots.md` | Which aiommbot 0.4.x features do the eleven company bots actually use, and which workarounds recur? |
| `10-plugin-systems.md` | What plugin models (Django apps, pluggy, entry points, Litestar, FastStream, Sphinx, Home Assistant) teach us? |
| `15-mattermost-session-revocation.md` | What does the Mattermost server do to an open WebSocket when the session is revoked or expires, and how does a client detect it? |
| `14-websocket-client-libraries.md` | Which WebSocket client library sits behind the gateway Protocol, and which HTTP client for REST? |
| `13-conversation-state-lifetime.md` | How do bot frameworks and stateless designs bound the lifetime of per-conversation state? |
| `12-error-boundary-conventions.md` | What do frameworks and task systems do by default when a handler raises, who owns the decision, and should the Core have a boundary? |
| `11-webhook-ingress-patterns.md` | How do peer frameworks bring HTTP callbacks into an event-driven core, and what does Mattermost's callback contract actually look like? |
