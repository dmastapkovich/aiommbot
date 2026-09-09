# Component design documents (LLD)

One file per component listed in the building-block view, created from
[`_template.md`](_template.md) by the `LLD: <component>` ticket that owns it. File name is the
component's `CONTEXT.md` term in kebab-case — except `key-value-store.md`, which is named after the
first of the two storage seams it specifies, because the two have no collective term.

*Wave* is the writing order decided by [ADR-0035](../../adr/0035-lld-order-is-a-topological-sort-of-structural-contract-dependencies.md):
a document waits only for the documents specifying a contract that appears in its own §3. Everything
in one wave may be written in parallel. The column is derived from the `blocked_by` dependencies on
the tickets and from nothing else — the tickets are the source of truth. A file is linked once it exists; readiness is the document's
status line and `TRACKER.md` §C.

| Component | Layer | File | Wave | Ticket |
|---|---|---|---|---|
| Event | Core | [`event.md`](event.md) | 1 | #86 |
| Signal | Core | `signal.md` | 1 | #58 |
| DependencyProvider | Core | `dependency-provider.md` | 1 | #59 |
| Generated model | Adapter | `generated-model.md` | 1 | #60 |
| Codec | Adapter | `codec.md` | 1 | #61 |
| Face | Adapter | `face.md` | 1 | #62 |
| KeyValueStore and LockProvider backends | Generic plugin | `key-value-store.md` | 1 | #63 |
| Filter | Core | `filter.md` | 2 | #64 |
| Extractor | Core | `extractor.md` | 2 | #65 |
| Sync executor | Core | `sync-executor.md` | 2 | #66 |
| Model generator | Adapter | `model-generator.md` | 2 | #67 |
| API client | Adapter | `api-client.md` | 2 | #68 |
| EventRegistry | Adapter | `event-registry.md` | 2 | #69 |
| Callback token | Adapter-specific plugin | `callback-token.md` | 2 | #70 |
| Router | Core | `router.md` | 3 | #71 |
| Exchange | Adapter | `exchange.md` | 3 | #72 |
| Workspace | Adapter | `workspace.md` | 3 | #73 |
| AuthLossDetector | Adapter | `auth-loss-detector.md` | 3 | #74 |
| Dispatcher | Core | `dispatcher.md` | 4 | #75 |
| Runtime | Adapter | `runtime.md` | 4 | #76 |
| IdentityCache | Adapter-specific plugin | `identity-cache.md` | 4 | #77 |
| Middleware | Core | `middleware.md` | 5 | #78 |
| ErrorBoundary | Core | `error-boundary.md` | 5 | #79 |
| Webhook | Adapter-specific plugin | `webhook.md` | 5 | #80 |
| WebSocketTransport | Adapter-specific plugin | `websocket-transport.md` | 5 | #81 |
| Bot | Core | `bot.md` | 6 | #82 |
| State | Generic plugin | `state.md` | 6 | #83 |
| FakeMattermost | Testing toolkit | `fake-mattermost.md` | 6 | #88 |
| Testing toolkit | Testing toolkit | `testing-toolkit.md` | 7 | #89 |
| Observability plugin | Generic plugin | `observability.md` | 7 | #92 |
