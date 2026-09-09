---
status: accepted
date: 2026-09-07
ticket: "#36"
---

# A typed outcome expresses a branch the immediate caller must take in normal operation; an exception expresses a broken contract or a failed dependency

Both styles are already in the design and no document says which to reach for. Typed outcomes were
chosen for Extractors (`Value | NoMatch | Invalid`,
[ADR-0014](0014-filters-and-extractors-with-closed-handler-signatures.md)), for dispatch (`Handled |
Unhandled | Failed`, [ADR-0020](0020-two-layer-middleware-chain.md)), for compare-and-set writes and
stale records (`Conflict`, `StaleState`, [ADR-0022](0022-state-plugin-model.md)) and for Callback
token verification (`Verified | Missing | Invalid | Expired | Replayed | ActorMismatch`,
[ADR-0024](0024-webhook-ingress-and-callback-security.md)); exceptions were chosen for the API
client, explicitly as "exceptions, not result unions" ([ADR-0027](0027-api-error-taxonomy.md)). Left
unstated, 32 component design documents would each pick by taste. We decided the rule that selects
the mechanism, and two riders that decide the cases where the first sentence is not enough:

- **The deciding question is who acts on the failure, not whether it is domain or infrastructure.**
  A typed outcome is right when the *immediate* caller must branch on it as part of normal
  operation — most sharply when that caller is walking a chain or a tree and a refusal means
  "continue with the next candidate". An exception is right when a contract was broken or a
  dependency failed, so that no caller between the failure and the boundary has anything useful to
  decide.
- **"All alternatives exhausted" becomes an exception at the boundary of the chain, never inside a
  participant.** A Filter that does not match, an Extractor that reports `NoMatch`, a Router subtree
  with no match — each is a participant declining; the Dispatcher is the boundary that turns the
  exhausted walk into `Unhandled`, and the ErrorBoundary is the boundary that turns an escaped
  exception into `Failed`. A participant that raises to mean "not me" makes the walk
  uninterruptible for the real errors.
- **Cardinality is the second discriminator: an exception reports the first failure, a typed
  outcome reports all of them.** This is why the check phase returns the full list of failures
  ([ADR-0016](0016-three-phase-start-with-checks.md)) and why Signal subscriber failures are
  collected rather than swallowed ([ADR-0017](0017-typed-async-lifecycle-signals.md)), while a
  single failed REST call raises.
- **One failure has exactly one representation.** A component never offers the same failure both as
  a member of an outcome union and as an exception; where both control flows are genuinely wanted,
  the choice is exposed to the call site as an overload on a `Literal` parameter and the type
  checker records which one was asked for.
- **An exception carries no payload** — the rule [ADR-0027](0027-api-error-taxonomy.md) already
  fixed for the API client, now general: identifiers, status and classification, never bodies,
  headers, query strings or tokens; Mattermost's short `message` and `error_id` are identifiers, not
  payload ([ADR-0027](0027-api-error-taxonomy.md)).

Evidence from django-modern-rest
([`docs/research/21`](../research/21-measured-facts-behind-the-rules.md)): its authentication
contract is `-> Self | None` — return `self` on success, return `None` when this participant
declines and the chain must continue, raise to fail the whole login immediately — and the chain
runner, not the participant, raises `NotAuthenticatedError` once every participant has declined. Its
`ThrottlingReport` docstring states the same contrast: unlike `TooManyRequestsError`, which reports
the first failing stat, the report collects them all.

## Considered options

- *Exceptions by default, typed outcomes only where an ADR already chose them* — rejected: it is
  the cheapest answer today and it is precisely what produces the divergence across 27 documents,
  because each author would reason from the nearest precedent rather than from a rule.
- *Typed outcomes inside the Core, exceptions only at the process boundary* — rejected: cleaner on
  paper and closer to errors-as-values, but it contradicts [ADR-0027](0027-api-error-taxonomy.md)
  and would force the API client to return a union on every call, which is the ergonomics
  [ADR-0027](0027-api-error-taxonomy.md) rejected for a client a script uses directly.
- *A `Result[T, E]` type in the Core* — rejected: the outcome unions we have are each closed and
  domain-named (`NoMatch` is not `Invalid`, `Conflict` is not `StaleState`), and a generic wrapper
  would flatten distinctions the handlers of those unions rely on while adding a name the glossary
  would have to defend against `Outcome`.

## Consequences

- Every component design document answers this rule in its failure-modes section by naming, for
  each failure it lists, whether it is an outcome or an exception and which boundary converts it.
- `Typed outcome` enters `CONTEXT.md` as the general term whose instances are the unions above;
  `Outcome` stays the dispatch-specific term it already is.
- The error taxonomy row of `docs/design/TRACKER.md` §D gains its missing piece:
  [ADR-0014](0014-filters-and-extractors-with-closed-handler-signatures.md),
  [ADR-0021](0021-core-error-boundary.md) and [ADR-0027](0027-api-error-taxonomy.md) fixed the
  values, the boundary and the exceptions, and this ADR fixes the choice between them.
