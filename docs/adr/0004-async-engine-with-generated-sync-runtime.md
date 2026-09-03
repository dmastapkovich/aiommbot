---
status: accepted
date: 2026-09-03
ticket: "#13"
---

# One asyncio engine; the synchronous face is limited to the REST client and runtime messaging and is generated from the async implementation

Both synchronous and asynchronous use are required: bots run on an asyncio WebSocket consumer,
while workers (Celery-style) and scripts need to send and edit messages synchronously.
django-modern-rest runs both because Django has two servers (WSGI and ASGI); FastStream and
Litestar run one async engine and execute synchronous handlers in a thread pool; mature clients
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

- The generation mechanism, the exact synchronous surface and its typing are decided in #22.
