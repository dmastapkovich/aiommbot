# 7. Deployment view

_Status: in progress (#40)._

How a bot built on aiommbot runs: one process with the WebSocket consumer, an optional Webhook behind
the application's ASGI server, processes without a Transport, the single-WebSocket-consumer
constraint, storage backends, what scales and what does not.

## Hosting the Webhook

**Nothing in the framework starts an HTTP server.** The Webhook exposes an ASGI callable
([ADR-0024](../adr/0024-webhook-ingress-and-callback-security.md)) and a host runs it: mounted in
the application's own ASGI app, handed to an ASGI server directly from a module that composes the
Bot and wraps its lifespan, or started by the CLI extra whose placement is #30's decision. For
example, `app.mount("/mm", webhook_app(bot))` with the Bot started in the ASGI lifespan.

## Topology is composition, not code

Both Transports are Plugins of the same Bot; the `ProcessProfile`
([ADR-0016](../adr/0016-three-phase-start-with-checks.md)) declares the role and the Checks enforce
it. The compositions below are illustrative; the public API shape is #31's.

| Shape | Composition | When |
|---|---|---|
| All in one | WebSocketTransport, Webhook and State in one Bot; profile `websocket_consumer=True, single_process=True` | small bot, one replica; in-memory State allowed |
| Split | Process A: WebSocketTransport only, `websocket_consumer=True`. Processes B×N: Webhook only, replicated behind a load balancer. Shared State on Redis | busy buttons and dialogs; callback fault tolerance |
| Plus workers | either shape, heavy work handed to a task queue through the Workspace, `SyncWorkspace` from a synchronous worker | operations that do not fit the reply deadline |

**The one hard constraint is protocol-level**: exactly one WebSocket consumer per bot account
([ADR-0005](../adr/0005-one-ingress-many-workers.md),
[ADR-0023](../adr/0023-websocket-gateway-resilience.md)); Webhook processes and workers replicate,
the socket does not. Checks enforce the declared role and the single-process condition of the
in-memory backend ([ADR-0003](../adr/0003-stateless-core-state-plugin-with-explicit-backend.md)); a
second consumer replica can stand by behind a `LockProvider` lease
([ADR-0023](../adr/0023-websocket-gateway-resilience.md)).
