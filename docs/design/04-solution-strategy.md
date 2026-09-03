# 4. Solution strategy

_Status: in progress (#13 settled the core; #14 and #38 complete the section)._

The handful of decisions that shape everything else. Each item is one paragraph and links to the
ADR that holds the decision.

## A small Core admitted by a two-condition test

The Core contains only what every bot needs identically or what is chat-specific with no library
equivalent; everything else is a Plugin, an extra or a recipe. The Core depends on the standard
library alone, ships in one distribution with the Adapter and first-party Plugins, and is enabled by
explicit composition in code. → [ADR-0002](../adr/0002-core-scope-two-condition-test.md)

## A stateless Core, state as a Plugin with an explicit backend

The Core holds nothing between events. Conversation state, isolation and backends belong to the
State Plugin, which cannot start without a backend; in-memory storage needs an explicit
single-process declaration. → [ADR-0003](../adr/0003-stateless-core-state-plugin-with-explicit-backend.md)

## One asyncio engine, a generated synchronous Runtime

Dispatch is asyncio-only; synchronous handlers run in a thread pool; the synchronous face exists
only for the Runtime and is generated from the asynchronous implementation.
→ [ADR-0004](../adr/0004-async-engine-with-generated-sync-runtime.md)

## One ingress, many workers

A bot is one WebSocket consumer, a replicable webhook ingress and any number of workers reached
through the Runtime; processes declare their role. → [ADR-0005](../adr/0005-one-ingress-many-workers.md)

## Composition over Core-owned Protocols, named patterns, strict typing

Bot has routers and plugins rather than inheriting them; the Core owns the Protocols that adapters
and plugins implement; patterns are named and justified per component; no singletons; immutable
events; declarative thin handlers; Python 3.12+ typing as the contract; fail closed.
→ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md)

## A tiny public root

`aiommbot` exports Core concepts only; the Adapter, Plugins and testing toolkit are explicit
subpackages; the rest is `_internal`. → [ADR-0007](../adr/0007-tiny-public-root-with-explicit-subpackages.md)

## One event envelope, type-driven routing, typed extraction

Every inbound event is `Event[P]`; the Adapter owns payload types and an explicit registry with
`RawEvent` as the fallback. Handlers subscribe by the annotation of their first parameter on a
router tree walked depth-first to the first match; dispatch returns a typed outcome; unreachable
handlers stop start-up. Filters are predicates, Extractors produce typed values, signatures are
closed. → [ADR-0012](../adr/0012-generic-event-envelope-with-adapter-payloads.md),
[ADR-0013](../adr/0013-type-driven-routing-with-a-typed-dispatch-outcome.md),
[ADR-0014](../adr/0014-filters-and-extractors-with-closed-handler-signatures.md)

## One Adapter, explicit Plugins, three-phase start, typed Signals

Exactly one Adapter supplies the platform vocabulary; every optional capability, transports
included, is a Plugin with a frozen declaration and narrow contribution Protocols, generic or
adapter-specific, ordered topologically by declared dependencies and configured through typed
frozen settings objects. The Bot composes, checks against a ProcessProfile with the full list of
failures, then starts; lifecycle notifications are typed async Signals.
→ [ADR-0015](../adr/0015-plugin-contract-and-composition.md),
[ADR-0016](../adr/0016-three-phase-start-with-checks.md),
[ADR-0017](../adr/0017-typed-async-lifecycle-signals.md)

## Still to be written here

Execution-model mechanism (#22), gateway resilience
strategy (#19), quality-by-mechanism toolchain (#23, #28).
