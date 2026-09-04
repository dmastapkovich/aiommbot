---
status: accepted
date: 2026-09-03
ticket: "#13"
amended-by: ADR-0029, ADR-0030, ADR-0031
---

# One asyncio engine; the synchronous face is limited to the REST client and runtime messaging and is generated from the async implementation

Both synchronous and asynchronous use are required: bots run on an asyncio WebSocket consumer,
while workers (Celery-style) and scripts need to send and edit messages synchronously.
django-modern-rest runs both because Django has two servers (WSGI and ASGI), and it bridges nothing
itself: the endpoint's colour is fixed at import time, the two pipelines are hand-written twins,
mixing colours in one controller is an error, and adaptation is Django's
`sync_to_async(thread_sensitive=True)` — a single serialised worker thread, not a pool. FastStream
runs one async engine and threads synchronous handlers automatically; Litestar runs one too but
refuses to guess and requires an explicit `sync_to_thread` (re-checked in #22, which corrects an
earlier misreading of Litestar here). Mature clients
(httpcore, PyMongo) generate their synchronous API from the asynchronous one (`docs/research/06`).
We decided: **the dispatch engine is asyncio-only**; synchronous user handlers are accepted and
run in a thread pool; a **synchronous face exists only for the Runtime** — the REST client and the
messaging helpers a process uses without consuming events — and it is **generated from the async
implementation** with a CI check, never hand-written.

## Considered options

- *Two engines, as in Django* — rejected: there is a single transport (asyncio WebSocket), so a
  synchronous engine would have no host and would double every test.
- *Runtime bridging (`anyio` blocking portal, `asyncio.run` per call)* — kept only as an escape
  hatch: ~50 µs per call and a second event-loop lifecycle to manage.
- *greenlet bridging (SQLAlchemy style)* — rejected: implicit I/O failure class and a C
  extension in the core path.

## Consequences

- The generation mechanism, the exact synchronous surface and its typing were decided in #22, which
  amended this decision in three places: the synchronous face is **not** generated but written as
  two thin drivers over a sans-I/O core, and it covers the API client and an Event-free `Workspace`
  rather than the whole Runtime ([ADR-0029](0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md));
  synchronous handlers are accepted only by an explicit declaration and run in the Bot's own bounded
  executor ([ADR-0030](0030-synchronous-callables-by-explicit-declaration.md)); the engine's
  concurrency discipline and the ownership of the event loop are fixed in
  [ADR-0031](0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md).
