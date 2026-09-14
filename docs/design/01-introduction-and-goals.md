# 1. Introduction and goals

_Status: reviewed (#37)._

`aiommbot` is an asynchronous Python framework for building Mattermost bots. It is a library: what
runs is a Bot process an application composes, and [§3](03-context-and-scope.md) draws the boundary
around that process. This section says what such a process must be able to do, which qualities the
design is optimised for and in what order, and who reads this catalogue.

## 1.1 Requirements overview

There is no separate requirements document. Scope is decided one ticket at a time on the wayfinder
map, [issue #1](https://github.com/dmastapkovich/aiommbot/issues/1), and every line below is
answered by an accepted decision rather than by an intention. Five functions carry 0.5.0; the line
between what the framework supplies and what the application supplies is
[§3.3](03-context-and-scope.md#33-scope-the-line-between-the-framework-and-the-application)'s.

| A bot built on aiommbot must be able to | Answered by |
|---|---|
| Consume one bot account's Mattermost event stream continuously, across network failures, server restarts and a revoked session | [ADR-0023](../adr/0023-websocket-gateway-resilience.md) |
| Deliver every event to application code chosen by the event's own type, through filters, two middleware layers and injected dependencies | [ADR-0012](../adr/0012-generic-event-envelope-with-adapter-payloads.md)…[ADR-0014](../adr/0014-filters-and-extractors-with-closed-handler-signatures.md), [ADR-0018](../adr/0018-core-owned-type-keyed-dependency-injection.md)…[ADR-0021](../adr/0021-core-error-boundary.md) |
| Act on the server through a typed REST surface, from asynchronous code and from synchronous code alike | [ADR-0025](../adr/0025-generated-dataclass-models-with-a-codec-protocol.md)…[ADR-0029](../adr/0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md) |
| Receive a button click or a dialog submission and answer it inside the window Mattermost allows, knowing the callback is its own | [ADR-0024](../adr/0024-webhook-ingress-and-callback-security.md) |
| Carry typed conversation state across events, isolated per conversation and bounded in time | [ADR-0022](../adr/0022-state-plugin-model.md) |

What the framework refuses instead of supplying — scheduling, retries, dead-letter queues, circuit
breakers, error reporting and metrics of its own — follows from the admission test of
[ADR-0002](../adr/0002-core-scope-two-condition-test.md), applied in
[ADR-0056](../adr/0056-the-framework-owns-no-scheduler.md) and
[ADR-0057](../adr/0057-reliability-middlewares-and-error-reporting-stay-outside.md).

## 1.2 Quality goals

Five goals of the **architecture**, ordered by priority. The order is what resolves a conflict:
where reliability and modifiability disagree, reliability wins. Each is stated as a situation rather
than as a word, because a word is not decidable; the full set of scenarios that decides it is
[§10](10-quality-requirements.md)'s, and §10.1 files every registered concern under exactly one of
these goals, so a goal with no concern under it would be a goal nothing tests.

| # | Goal | The situation it has to survive | Decided by |
|---|---|---|---|
| 1 | **Reliability** | The socket dies mid-burst at three in the morning and nobody is awake: the bot reconnects, resumes from its sequence, handles each post once, and when the host finally stops it, stops inside the budget it declared | [§10.2](10-quality-requirements.md#102-reliability), 7 scenarios |
| 2 | **Correctness by mechanism** | A composition that cannot work — a Handler nothing can reach, an in-memory backend in a replicated process — never opens a socket: the check phase refuses it with every failure listed, and a tool rather than a reviewer is what caught the type that got it there | [§10.3](10-quality-requirements.md#103-correctness-by-mechanism), 4 scenarios |
| 3 | **Testability** | A team writes a storage backend of its own and an application exercises its whole bot, and neither needs a Mattermost server, a network or a second composition path | [§10.4](10-quality-requirements.md#104-testability), 1 scenario |
| 4 | **Modifiability** | Replacing the transport, the store or the observability backend is one line of composition, and the build refuses the import that would have made the replacement impossible | [§10.5](10-quality-requirements.md#105-modifiability), 3 scenarios |
| 5 | **Security** | A button the bot issued an hour ago comes back with its `context` edited: no Handler runs, the caller still gets an answer in time, and nothing written to a log along the way carries the token, the message text or the user's data | [§10.6](10-quality-requirements.md#106-security), 2 scenarios |

**Performance is not one of them.** No throughput, latency or memory target exists for 0.5.0 and
none is invented here: the framework is measured on the paths it owns rather than on numbers a
library cannot observe. Setting them is open work the map tracks.

## 1.3 Stakeholders

Who reads this catalogue and what they come here for. A row exists because someone needs something
*from this documentation*; the parties a *running* Bot process exchanges messages with are a
different question and are [§3.1](03-context-and-scope.md#31-business-context)'s. Contacts are
deliberately absent: the project is public and every party reaches it through the issue tracker.

| Role | What they expect of this catalogue |
|---|---|
| Application developer | The contract of every seam, the line between framework and application, and the Plugin list each Process shape needs |
| Third-party plugin author | The Plugin contract, what the host promises a Plugin, and the Conformance suite that proves an implementation |
| Framework contributor | [`engineering-style.md`](engineering-style.md), the layer contract of [§5](05-building-block-view.md), and the component design document of whatever they touch |
| AI coding agent | `AGENTS.md`, [`CONTEXT.md`](../../CONTEXT.md) and the ADRs — enough context to contribute without re-deriving a settled decision |
| Operator | [§7](07-deployment-view.md): what a host must promise a process, which credentials each Process shape needs, and what the probes and the log records mean |
