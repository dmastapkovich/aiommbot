---
status: accepted
date: 2026-09-09
ticket: "#25"
---

# One stateful `FakeMattermost` is the only platform double, and its ports, its faults and its events are its own surface

[ADR-0029](0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md) and
[ADR-0023](0023-websocket-gateway-resilience.md) each required an in-memory implementation of a
network seam, which would have left a test talking to two unrelated objects that share no idea of
what the server knows. We decided on **one stateful in-memory server, `FakeMattermost`**, holding
users, channels, posts and reactions, and exposing that state through **ports**: `http`, one class
implementing both `HTTPTransport` and `SyncHTTPTransport` as ADR-0029 requires, and `websocket`,
implementing `WebSocketConnection`. It is the only object a test configures, and there is no second
double of the platform anywhere in the toolkit.

- **A fault is a fact about the server, like a channel is.** A test schedules typed outcomes —
  a status with an `AppError` ([ADR-0027](0027-api-error-taxonomy.md)) on the next call of one
  `Operation`, a close code, silence past the heartbeat deadline, a revoked session, a gap in the
  sequence number — and the retry policy, the reconnect table and the `AuthLossDetector` are
  exercised through the same surface as the happy path. This is what removes the need for a
  scripted transport beside the server, including in the conformance suites of both Faces.
- **A test prepares its own server by seeding and substitution, never by subclassing.** It
  constructs the server, seeds the world it needs, replaces the behaviour of an individual
  `Operation` with a typed handler where the world is not enough, and passes the instance to
  `TestBot` ([ADR-0046](0046-testbot-wraps-the-composed-bot.md)) or to its own fixture.
  Subclassing one of our classes is `ST-PAT-07`'s banned pattern and no extension point here.
- **The server records; the test asserts on the record.** Every call arrives as a frozen `ApiCall`,
  so an assertion reads as what the bot achieved rather than as how it called (`ST-TST-07`).
- **Events have one shape whether they are built or provoked.** The toolkit's typed event builders
  construct an `Event` for the first-class payloads without a server, and a mutation of the server
  produces the same event through the same builders and puts it on the socket, so a unit test of a
  Filter and an end-to-end test of a bot never disagree about what an event looks like.

## Considered options

- *No server at all: a scripted `HTTPTransport` double plus a frame queue on the socket* —
  rejected: it is the cheapest thing that satisfies ADR-0023 and ADR-0029 and it is what the peers
  ship, but "a user wrote in a channel and the bot answered" is then two unrelated scripts the test
  has to keep consistent by hand.
- *A server plus a thin scripted transport for the low-level suites* — rejected: it keeps the
  server small at the price of two doubles of one seam inside one layer, both of which have to pass
  the same conformance suite.
- *A real server in a container for everything* — rejected: it is the only thing that cannot drift,
  and it is why `tests/integration/` exists
  ([ADR-0039](0039-src-layout-with-tests-and-examples-beside-the-package.md)); it is not what a unit
  suite with a per-test timeout can run.

## Consequences

- The server is a **component** of the testing toolkit layer with its own design document, not a
  part of the toolkit's: it holds state, it has invariants and it has failure modes of its own
  (§5.9 of [`05-building-block-view.md`](../design/05-building-block-view.md)).
- It can lie, and two mechanisms keep it honest: it answers with the generated models through the
  `Codec` seam ([ADR-0025](0025-generated-dataclass-models-with-a-codec-protocol.md)), so a REST
  reply that the spec does not describe is unconstructible, and the resume, sequence and dead-queue
  behaviour of its socket port follows [`docs/research/01`](../research/01-mattermost-websocket-protocol.md)
  rather than invention. Where a test needs the real server, it belongs to `tests/integration/`.
- The `websocket` port is what makes ADR-0023's exit table testable without a network, so the
  fidelity that matters most is the socket's, not the REST surface's.
