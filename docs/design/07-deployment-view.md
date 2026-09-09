# 7. Deployment view

_Status: in progress (#40)._

How a bot built on aiommbot runs: one process with the WebSocket consumer, an optional Webhook
behind the application's ASGI server, processes without a Transport, the
single-WebSocket-consumer constraint, storage backends, what scales and what does not.

## Hosting the ASGI callables

**Nothing in the framework starts an HTTP server** — not a Plugin, not the Core, and not the
`aiommbot` command
([ADR-0058](../adr/0058-the-command-is-a-console-script-behind-the-click-extra.md)). Two Plugins
expose an ASGI callable and a host runs it: the Webhook's `webhook_app(bot)`
([ADR-0024](../adr/0024-webhook-ingress-and-callback-security.md)) and the Health Plugin's
`health_app(bot)`
([ADR-0061](../adr/0061-health-is-a-generic-plugin-over-application-supplied-checks.md)). Either is
mounted in the application's own ASGI app or handed to an ASGI server from a module that
composes the Bot and wraps its lifespan — for example `app.mount("/mm", webhook_app(bot))` beside
`app.mount("/", health_app(bot))`, with the Bot started in the ASGI lifespan.

A process whose only connection is the outbound socket has no HTTP of its own, so it composes the
Health Plugin and runs `health_app(bot)` under a small server of its own; that is what Slack's Bolt
example and `cloudflared` both do
([`docs/research/26`](../research/26-schedule-reliability-and-probe-primitives.md) §7.4). The probe
paths are `/livez` and `/readyz`; liveness stays true for the whole drain, so a `livenessProbe`
never kills a bot that is finishing its last events, and readiness turns false the moment the drain
begins (ADR-0061).

## Topology is composition, not code

Both Transports are Plugins of the same Bot; the `ProcessProfile`
([ADR-0016](../adr/0016-three-phase-start-with-checks.md)) declares the role and the Checks enforce
it. The compositions below are illustrative; the public API shape is #31's.

| Shape | Composition | When |
|---|---|---|
| All in one | WebSocketTransport, Webhook, State and Health in one Bot; profile `websocket_consumer=True, single_process=True` | small bot, one replica; in-memory State allowed |
| Split | Process A: WebSocketTransport and Health, `websocket_consumer=True`. Processes B×N: Webhook and Health, replicated behind a load balancer. Shared State on Redis, FloodControl beside it | busy buttons and dialogs; callback fault tolerance |
| Plus workers | either shape, heavy work handed to a task queue through the Workspace, `SyncWorkspace` from a synchronous worker | operations that do not fit the reply deadline |

**The one hard constraint is protocol-level**: exactly one WebSocket consumer per bot account
([ADR-0005](../adr/0005-one-ingress-many-workers.md),
[ADR-0023](../adr/0023-websocket-gateway-resilience.md)); Webhook processes and workers replicate,
the socket does not. Checks enforce the declared role and the single-process condition of the
in-memory backend ([ADR-0003](../adr/0003-stateless-core-state-plugin-with-explicit-backend.md)); a
second consumer replica can stand by behind a `LockProvider` lease
([ADR-0023](../adr/0023-websocket-gateway-resilience.md)).
