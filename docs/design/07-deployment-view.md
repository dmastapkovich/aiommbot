# 7. Deployment view

_Status: in progress (inputs settled by #19, #20, #24; #40 completes the section)._

How a bot built on aiommbot runs: single process with WebSocket consumer, optional webhook server,
runtime-only processes, the single-WebSocket-consumer constraint, storage backends, what scales and
what does not.

## Inputs settled so far

**Nothing in the framework starts an HTTP server.** The webhook plugin exposes
`webhook_app(bot) -> ASGIApp` (ADR-0024); a host runs it. Three hosting shapes are supported and
documented:

- **The application's own ASGI app** (FastAPI, Litestar): `app.mount("/mm", webhook_app(bot))`,
  with the `Bot` started as a background task inside the ASGI lifespan. uvicorn or hypercorn is
  the process host; the bot lives in its event loop.
- **No application app**: hand `webhook_app(bot)` to uvicorn directly from a small module that
  composes the bot and wraps its lifespan.
- **CLI extra** (#30): `aiommbot run myapp:bot --serve host:port` starts uvicorn programmatically as
  a task next to the bot's transports in one loop. Convenience of the CLI, not a capability of the
  Core or the plugin.

**Topology is composition, not code.** Both transports are plugins of the same `Bot`; the
`ProcessProfile` (ADR-0016) declares the role and the start-up checks enforce it.

| Shape | Composition | When |
|---|---|---|
| All in one | `Bot(adapter, plugins=[WebSocketTransport(), Webhook(), State(...)])`, profile `websocket_consumer=True, single_process=True` | small bot, one replica; in-memory State allowed |
| Split | Process A: `WebSocketTransport` only, `websocket_consumer=True`. Processes B×N: `Webhook()` only, replicated behind a load balancer. Shared State on Redis | busy buttons and dialogs; ingress fault tolerance |
| Plus workers | either shape, heavy work handed to Celery/taskiq/… through the sync or async Runtime | operations that do not fit the 10 s reply deadline |

**The one hard constraint is protocol-level**: exactly one WebSocket consumer per bot account
(ADR-0005, ADR-0023); the webhook ingress and workers replicate, the socket does not. Checks refuse
a second consumer without the declared role, and an in-memory State backend without
`single_process` (ADR-0003). An optional lease through a distributed `LockProvider` turns a second
consumer replica into a standby (ADR-0023).

## Still to be written here (#40)

`ProcessProfile` fields and their check matrix; C4 deployment diagrams for the three shapes;
Kubernetes notes (readiness, SIGTERM and the 25 s drain budget, one replica for the consumer,
HPA for the ingress); storage backends per shape; what scales and what does not.
