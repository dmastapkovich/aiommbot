---
status: accepted
date: 2026-09-04
ticket: "#22"
---

# The synchronous face covers only the API client and an Event-free `Workspace`, and is produced by a sans-I/O core with two thin drivers instead of async-to-sync code generation

ADR-0004 promised a synchronous face "generated from the async implementation" for the whole
Runtime. Usage mining of the frozen 0.4.8 line kills the premise: `SyncBotRuntime` was 250 lines of
hand-mirrored facade over a background thread owning its own event loop, with `future.result()` and
no timeout, three separate `fork()` warnings in the documentation, one reflection test guarding the
mirror, a recurring release chore to mirror every new method — and **zero consumers** across the
eleven company bots, in source, tests or scripts (no Celery or Django anywhere). The need it was
built for is real — three bots message users from outside a handler — and all three satisfy it with
the *asynchronous* Runtime in-process. Meanwhile every reference library that generates a sync twin
generates only the wide, boring surface and hand-writes concurrency, cancellation and I/O:
httpcore's `_synchronization.py` and `_backends/`, psycopg's `_acompat.py`, and pymongo's
never-converted test list (`test_locks`, `test_concurrency`, `test_async_cancellation`,
`test_async_loop_safety`) name exactly the semantics that do not survive unasyncing. We decided:

- **Two surfaces get a synchronous face, and no others.** `SyncMattermostClient` (ADR-0026) and
  `SyncWorkspace`. The bare name stays asynchronous, the `Sync` prefix marks the twin.
- **`Workspace` is the Event-free layer, split out of the Runtime.** It is a public, independently
  constructible object holding `send(channel_id, ...)`, `send_direct(UserRef, ...)`, `ephemeral`,
  `upload`, `download`, `users.resolve` and `channels.direct`. The `Runtime` composes it and keeps
  the public helper set ADR-0028 fixed; the Event-bound helpers — `answer`, `reply`, `update`,
  `delete`, `open_dialog` — take channel, `root_id` and `trigger_id` from an Event, are meaningless
  outside the loop and stay asynchronous only. A script that needs a direct message calls
  `SyncWorkspace.send_direct`, not three API calls.
- **No async-to-sync tool enters the toolchain.** `Operation` descriptors are pure data with no
  face at all; the spec generator (ADR-0025) emits the resource methods for *both* faces, which
  costs it nothing; the retry decision, the error mapping and the pagination advance are sans-I/O
  pure functions tested once (ADR-0006); what remains per face is a thin driver — build the
  request, send it, parse the response — because httpx2 shares `build_request`, `Request` and
  `Response` between its faces and its two client method sets differ only in `close`/`aclose`,
  `read`/`aread`, `iter_*`/`aiter_*` and the context-manager dunders.
- **`SyncHTTPTransport` is a paired Core Protocol.** `HTTPTransport` exists as insurance against the
  httpx2 fork risk, and insurance that covers one face only is not insurance; httpx2's own
  `BaseTransport`/`AsyncBaseTransport` are plain classes, not Protocols, so there is nothing to
  reuse and the pair costs four lines. The in-memory double in `aiommbot.testing` implements **both
  faces in one class**, as httpx2's `MockTransport` does, so the test seam does not double.
- **Credentials.** The synchronous face accepts a `str` or a `SyncTokenProvider`; `TokenProvider`
  (ADR-0023) stays asynchronous and belongs to the Bot and the asynchronous client. `IdentityCache`
  is unavailable to the synchronous face — `KeyValueStore` is asynchronous and ADR-0028 resolves
  without a cache by default anyway.
- **Duality is held by mechanism, not by review.** The committed-output `--check` of ADR-0025 covers
  both faces; typing tests assert that `MattermostClient` and `SyncMattermostClient` satisfy their
  Protocols; one parametrised conformance suite drives both faces through the shared in-memory
  double; a typed parity test asserts the two faces expose the same method names — 0.4.8's single
  reflection test, taken as far as the type checkers can carry it.
- **Threads.** The synchronous client documents *one instance per thread* rather than promising
  thread safety: httpx2 runs no free-threaded job in CI, states nothing about `Client` thread
  safety, and a shared `Client(http2=True)` corrupts the h2 state machine (upstream PR #1153, open).
  HTTP/2 stays off by default (ADR-0026), so the corruption path is not ours by default.

## Considered options

- *A full `SyncRuntime` mirroring the Runtime, as ADR-0004 wrote it* — rejected: it is the exact
  artefact that scored 0/11 in production, and every new helper would be a mirroring chore.
- *Only `SyncMattermostClient`, no helpers* — rejected: `send_direct` becomes resolve plus
  create-direct-channel plus create-post in every script, which is the copy-paste ADR-0028 removed.
- *No synchronous face at all* — rejected: the requirement to serve scripts, migrations and
  synchronous workers stands, and the cost after this decision is a few dozen lines.
- *`unasyncd` 0.10.1* — rejected: its `--check` reports "0 files would be transformed" against a
  demonstrably stale target, it leaves `TypeVar("AsyncX")` and `bound="AsyncX"` unrenamed — which is
  precisely our `Protocol` and `TypeVar` code and makes all four checkers (ADR-0009) fail — it is a
  single-maintainer dependency, an invalid config key was silently ignored for a downstream user,
  Litestar's own use has decayed to one vestigial file, and `sqlspec` in the same organisation chose
  ~4,300 hand-written lines over adopting it.
- *`unasync` 0.6.0, or our own libcst/AST script* — rejected: `unasync`'s last release predates this
  design by two years, it has no `--check`, it overwrote the source file on a `fromdir` mismatch, and
  neither it nor `unasyncd` rewrites `Coroutine[Any, Any, T]`; an AST rewriter makes the output
  interpreter-version-dependent, which is why psycopg pins one CPython for generation.
- *Runtime bridging over a background loop thread* — rejected: that is 0.4.8's mechanism, and its
  documented hazard is that the thread does not survive `fork()`.

## Consequences

- ADR-0004 is amended: the synchronous face is not generated, and its scope is the client plus
  `Workspace`. ADR-0028's helper set is split into an Event-free layer and Event-bound sugar.
- The Adapter carries two thin drivers that must stay in step; the parity test and the shared
  conformance suite are what keep them honest.
- The `Workspace` component and the two drivers each need a design document from the LLD inventory
  (#41), and the conformance and parity suites belong to the testing toolkit (#25).
