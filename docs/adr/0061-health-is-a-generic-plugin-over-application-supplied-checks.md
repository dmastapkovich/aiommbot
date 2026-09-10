---
status: accepted
date: 2026-09-09
ticket: "#30"
amends: [ADR-0024, ADR-0049]
amended-by: [ADR-0065]
---

# Health is a generic Plugin serving `/livez` and `/readyz` as a bare ASGI application: liveness runs no check, readiness derives from the Signals plus checks the application supplies, and the aggregate is cached

A Bot deployed in the split shape of [§7](../design/07-deployment-view.md) runs a process whose only
connection is an outbound WebSocket, and Kubernetes has nothing to probe on it. The framework
already holds the two facts that matter — whether the Bot is started or draining, and whether each
Transport is connected — so the endpoint is ours to offer; but *what else* counts as ready is the
application's knowledge, which is why this is a Plugin with a settings object and not a fixed route.
Nothing in the Python ecosystem lets an application contribute a check to a framework's health
endpoint ([`docs/research/27`](../research/27-application-contributed-readiness-checks.md) §2, §7).
We decided:

- **One generic Plugin, `Health`, and `health_app(bot) -> ASGIApp`.** A bare ASGI callable with no
  dependency, mirroring the Webhook's ([ADR-0024](0024-webhook-ingress-and-callback-security.md));
  the application hands it to the server it already runs, mounts it beside its own app, or gives the
  consumer process a server of its own. **Nothing in the framework starts one**
  ([ADR-0002](0002-core-scope-two-condition-test.md)), including the command
  ([ADR-0058](0058-the-command-is-a-console-script-behind-the-click-extra.md)).
- **Two paths, `/livez` and `/readyz`**, in a typed `HealthPaths` the application may change. These
  are the names the Kubernetes API server itself serves, where **`/healthz` has been deprecated
  since v1.16**, and the two Spring Boot publishes under `add-additional-paths`. `/livez` is the
  restart signal and `/readyz` the traffic signal, in Kubernetes' own words.
- **Liveness runs no check and reads no dependency.** It answers 204 for as long as the process can
  still make progress — *including for the whole Drain* — and 503 only once the Bot has stopped on a
  `FatalError` ([ADR-0021](0021-core-error-boundary.md)) while the process is still up. Kubernetes
  requires a liveness probe to indicate only an unrecoverable failure, and Spring keeps liveness
  `CORRECT` across a graceful shutdown for the same reason. The rule earns its keep away from
  Kubernetes: the kubelet stops liveness and startup probes at the first step of termination, so
  there it cannot kill a draining container at all
  ([`docs/research/29`](../research/29-kubernetes-fields-a-drain-depends-on.md) §5) — but a
  container-level health check, a service manager or a supervisor keeps probing throughout, and a
  liveness that failed on the Drain would restart a bot that is finishing its last events.
- **Readiness is the conjunction of four things**: the Bot is started, it is not draining, every
  Transport in the plugin list is connected or `Standby` as its Signals last reported
  ([ADR-0017](0017-typed-async-lifecycle-signals.md), ADR-0023,
  [ADR-0065](0065-a-transport-waiting-on-the-consumer-lease-is-standby-and-counts-as-ready.md)), and
  every check the application supplied passes. A Transport that publishes no state at all counts as
  ready from the start, and a process with no Transport is ready as soon as it has started.
  Readiness turns false the moment the Drain begins — the half no project in the survey implements —
  and the readiness probe is the one that keeps running through termination
  ([`docs/research/29`](../research/29-kubernetes-fields-a-drain-depends-on.md) §5).
- **A check is a named object with its own bound, and it arrives in the settings.** A frozen
  `ReadinessCheck(name, run, timeout)` in `Health(checks=(...))`; there is **no eighth
  `Contributes*` Protocol** and no registry, so
  [ADR-0015](0015-plugin-contract-and-composition.md) is unchanged and #85's question about the rank
  of the seven is untouched. A Plugin with a readiness fact of its own exposes a `ReadinessCheck`
  that the composition passes in, which keeps the contribution explicit like everything else
  ([ADR-0002](0002-core-scope-two-condition-test.md)).
- **Checks run concurrently, each under its own timeout and all under one deadline, and a check that
  throws is one failed check.** It is logged as a WARNING and never becomes a 5xx. The references
  are weak here and it is worth being better than them: Spring runs contributors sequentially with
  no timeout at all — only a warning logged *after* a slow one finishes — ASP.NET Core's per-check
  timeout defaults to infinite, and `django-health-check` 3.x let a throwing check take the whole
  endpoint down before 4.x fixed it (same note, §4).
- **The aggregate is cached for `cache_ttl`.** A probe arrives every 10 s by default, per replica
  and per probe kind, and re-running a dependency check on each is how a health endpoint becomes
  load — `django-health-check` documents its own endpoint as a denial-of-service vector for exactly
  this. Nothing in maintained Python caches a health result; the two mechanisms that avoid the cost
  are ASP.NET Core's timer-driven publisher and arq's Redis key with a TTL, and a short TTL over the
  pull path is the cheaper of the two because it introduces no task of ours.
- **The body is empty and stays empty.** Kubernetes reads only the status code, counts 200–399 as
  success and stops reading a body at 10 KiB. The name of a failing check goes to the log, never to
  the response: the endpoint is unauthenticated, Spring defaults `show-details` to `never`, and
  `REDACTED_FIELDS` ([ADR-0055](0055-one-redaction-list-over-two-sinks.md)) governs what may be
  written down at all. Nothing per probe is logged.

## Considered options

- *A Core helper rather than a Plugin* — rejected by the maintainer: a bot author must be able to
  add readiness facts of their own, and a fixed route cannot take a settings object, a Check or a
  document of its own. The cost is accepted and named below.
- *An eighth `ContributesReadiness` Protocol, so a Plugin answers "are you ready?" the way
  `ContributesStats` answers with a snapshot* — rejected: the Signals already carry every transport
  transition, and a Protocol whose only implementations would be ours buys nothing that a
  `ReadinessCheck` in the settings does not.
- *Reading readiness out of `bot.stats()`* — rejected: `CONTEXT.md` defines the Stats snapshot as
  the reading of every **bounded resource** and its `_Avoid_` list names "health check (that is a
  runtime probe)" explicitly, so the snapshot was defined as not being this.
- *One endpoint only* — rejected: for a Pod with no Service a readiness probe changes no traffic,
  but the Pod `Ready` condition still drives `minReadySeconds`, `maxUnavailable`,
  `progressDeadlineSeconds` and PodDisruptionBudget, so it paces a rollout and protects a draining
  consumer from voluntary eviction (same note, §3).
- *A body carrying the failing check names, as Spring and ASP.NET Core can* — rejected: it is an
  unauthenticated endpoint and the operator's copy of the reason is the log.

## Consequences

- `Health` is a component of §5.7 with a `LLD: Health` ticket in the writing order of
  [ADR-0035](0035-lld-order-is-a-topological-sort-of-structural-contract-dependencies.md), after the
  Signal and Bot documents its readiness is derived from.
- The Webhook carries no health route of its own
  ([ADR-0024](0024-webhook-ingress-and-callback-security.md)): there is one health surface, one pair
  of paths and one document, and a Webhook process mounts `health_app(bot)` beside
  `webhook_app(bot)`.
- The closed table of [ADR-0049](0049-what-the-framework-makes-observable.md) gains one row —
  whether the process is alive and ready, carried by the Health Plugin's two paths, shipping nothing
  by default because the Plugin is composed explicitly. It remains closed.
- The failure a Plugin makes possible is real and is documented: a probe that answers 404 because
  the Plugin is not in the composition. The Plugin's own document states it, and the deployment view
  says what to compose for each process shape.
