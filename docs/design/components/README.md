# Component design documents (LLD)

One file per component listed in the building-block view, created from
[`_template.md`](_template.md) by the `LLD: <component>` ticket that owns it. File name is the
component's `CONTEXT.md` term in kebab-case — except `key-value-store.md`, which is named after the
first of the two storage seams it specifies, because the two have no collective term.

*Wave* is the writing order decided by [ADR-0035](../../adr/0035-lld-order-is-a-topological-sort-of-structural-contract-dependencies.md):
a document waits only for the documents specifying a contract that appears in its own §3. Everything
in one wave may be written in parallel. The column is derived from the `blocked_by` dependencies on
the tickets and from nothing else — the tickets are the source of truth.

| Component | File | Wave | Status | Ticket |
|---|---|---|---|---|
| Event | [`event.md`](event.md) | 1 | reviewed | #57 |
| Signal | [`signal.md`](signal.md) | 1 | not started | #58 |
| DependencyProvider | [`dependency-provider.md`](dependency-provider.md) | 1 | not started | #59 |
| Generated model | [`generated-model.md`](generated-model.md) | 1 | not started | #60 |
| Codec | [`codec.md`](codec.md) | 1 | not started | #61 |
| Face | [`face.md`](face.md) | 1 | not started | #62 |
| KeyValueStore and LockProvider backends | [`key-value-store.md`](key-value-store.md) | 1 | not started | #63 |
| Filter | [`filter.md`](filter.md) | 2 | not started | #64 |
| Extractor | [`extractor.md`](extractor.md) | 2 | not started | #65 |
| Sync executor | [`sync-executor.md`](sync-executor.md) | 2 | not started | #66 |
| Model generator | [`model-generator.md`](model-generator.md) | 2 | not started | #67 |
| API client | [`api-client.md`](api-client.md) | 2 | not started | #68 |
| EventRegistry | [`event-registry.md`](event-registry.md) | 2 | not started | #69 |
| Callback token | [`callback-token.md`](callback-token.md) | 2 | not started | #70 |
| Router | [`router.md`](router.md) | 3 | not started | #71 |
| Exchange | [`exchange.md`](exchange.md) | 3 | not started | #72 |
| Workspace | [`workspace.md`](workspace.md) | 3 | not started | #73 |
| AuthLossDetector | [`auth-loss-detector.md`](auth-loss-detector.md) | 3 | not started | #74 |
| Dispatcher | [`dispatcher.md`](dispatcher.md) | 4 | not started | #75 |
| Runtime | [`runtime.md`](runtime.md) | 4 | not started | #76 |
| IdentityCache | [`identity-cache.md`](identity-cache.md) | 4 | not started | #77 |
| Middleware | [`middleware.md`](middleware.md) | 5 | not started | #78 |
| ErrorBoundary | [`error-boundary.md`](error-boundary.md) | 5 | not started | #79 |
| Webhook | [`webhook.md`](webhook.md) | 5 | not started | #80 |
| WebSocketTransport | [`websocket-transport.md`](websocket-transport.md) | 5 | not started | #81 |
| Bot | [`bot.md`](bot.md) | 6 | not started | #82 |
| State | [`state.md`](state.md) | 6 | not started | #83 |
