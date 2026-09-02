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
