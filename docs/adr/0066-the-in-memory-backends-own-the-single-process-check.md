---
status: accepted
date: 2026-09-10
ticket: "#40"
amends: [ADR-0003, ADR-0016, ADR-0022]
---

# The in-memory storage backends contribute the single-process Check themselves, so every consumer of the seam inherits it

The Check that an in-memory backend needs `ProcessProfile.single_process` was written when
conversation state was the only thing stored
([ADR-0003](0003-stateless-core-state-plugin-with-explicit-backend.md)). Four capabilities now read
the same seams — State ([ADR-0022](0022-state-plugin-model.md)), the Webhook's `NonceStore`
([ADR-0024](0024-webhook-ingress-and-callback-security.md)), `IdentityCache`
([ADR-0028](0028-runtime-helpers-and-identity-resolution.md)) and FloodControl
([ADR-0060](0060-flood-control-and-delivery-dedup-are-one-generic-plugin.md)) — and three of them
start silently on a process-local store in a replicated deployment. We decided that **the in-memory
`KeyValueStore` and `LockProvider` contribute the Check**, because being process-local is a fact
about the implementation and not about any of its consumers; the State plugin contributes it no
longer. One error-severity Check, named after the storage rather than after a feature, covers every
present consumer and every future one without being copied.

## Considered options

- *One Check per consumer* — rejected: four copies of one rule, each free to drift, and the fifth
  consumer starts silently again.
- *Leaving it with State* — rejected: a Webhook process replicated behind a load balancer with an
  in-memory nonce store passes start-up and then accepts a replayed callback on any replica that has
  not seen it.
- *Refusing the in-memory backends outside tests* — rejected: they are what makes a first bot run
  without a Redis, and the declaration plus the Check is what keeps that honest
  ([ADR-0003](0003-stateless-core-state-plugin-with-explicit-backend.md)).

## Consequences

- The Check is a part of `key-value-store.md`; `state.md` cites it instead of owning it.
- The rule reaches only the backends we ship. An application that supplies its own process-local
  implementation of either seam is outside it, which is one more reason the conformance suite
  ([ADR-0047](0047-a-conformance-suite-per-core-seam.md)) is where an external backend proves what
  it is.
