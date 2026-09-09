---
status: accepted
date: 2026-09-09
ticket: "#29"
amends: [ADR-0041]
---

# Observability ships as one generic plugin behind two library-named extras, emits under the OpenTelemetry conventions with the transport stream as the destination, takes the Prometheus registry as an argument, and bounds its own cardinality with an allow-list and a start-up Check

`opentelemetry-api` and `prometheus-client` are never dependencies of this distribution: everything
the framework offers for observability is an optional library and an offer the application may
decline in favour of its own. That is also what every peer does — none keeps telemetry in core
dependencies, and OpenTelemetry itself advises "While your instrumentation stabilizes, consider
shipping it as a separate package, so that it never causes issues for users who don't use it"
([`docs/research/23`](../research/23-dispatch-observability-in-async-frameworks.md) §1.4, §3). We
decided:

- **Two extras, named after their libraries** under the rule of
  [ADR-0041](0041-default-dependencies-and-one-extra-per-optional-library.md): `opentelemetry`
  installs `opentelemetry-api` — the API only, never the SDK, which is the application's — and
  `prometheus` installs `prometheus-client`. Each is the spelling the ecosystem uses for the
  library rather than its exact distribution name, the licence `paseto` already took. The four
  default dependencies are unchanged.
- **One component, two plugins.** `PrometheusPlugin` and `OpenTelemetryPlugin` each carry a
  `PluginSpec` and a typed frozen settings object, and both live in one component because their
  design is one design: the same facts, the same label rules, the same storage decorators, the same
  snapshot reading. Each raises `MissingExtraError` in its constructor when its library is absent
  (`ST-MOD-08`).
- **Names follow the conventions, and the destination is the stream.** The HTTP client set is
  Stable and is followed exactly
  ([`docs/research/17`](../research/17-http-client-observability.md) §1). Dispatch follows the
  messaging conventions with `messaging.system="mattermost"` — the registry's enumeration has no
  chat value and says "otherwise, a custom value MAY be used" — `messaging.operation.type="process"`
  and span kind CONSUMER. **The destination is the Transport's stream, one value per process, and
  never the channel**: a bot subscribes to one stream and the channel is a property of the message,
  so reading the channel as the destination would put an unbounded platform identifier into the span
  name that the conventions build from the destination. The event kind is a separate attribute.
- **The application owns the registry.** Each plugin takes its `CollectorRegistry` as a required
  argument and never touches the process-global default, and no metric is constructed at module
  scope. Writing to the default registry makes two Bots in one process a
  `ValueError: Duplicated timeseries in CollectorRegistry` and makes a re-import under a test runner
  the same, and the Prometheus client specification requires the escape hatch to exist: "There MUST
  be a way to have metrics not register to the default CollectorRegistry"
  ([`docs/research/23`](../research/23-dispatch-observability-in-async-frameworks.md) §4).
- **Cardinality is bounded by two mechanisms, and the ADR says whose policy that is.** No primary
  source publishes a mechanical rule — Prometheus gives prose numbers and OpenMetrics states it
  "does not prescribe any particular limits" (same note, §1.6) — so this is the framework's policy
  layered on top of the ecosystem, not compliance with it. **The rule:** a label value comes only
  from a set enumerable at start-up — the EventRegistry's kinds, the frozen Router's Handler names,
  the generated `Operation` ids, the `Outcome` class, the HTTP method, the status code, an
  exception's qualname, an `AppError.id` — and from nothing else. **The mechanisms:** a test asserts
  that every declared label key lies in one named allow-list and that the allow-list does not
  intersect `REDACTED_FIELDS` ([ADR-0055](0055-one-redaction-list-over-two-sinks.md)); and a typed
  Check ([ADR-0016](0016-three-phase-start-with-checks.md)) multiplies the declared cardinalities at
  the check phase — the Router is frozen and the vocabulary registered by then, so the product is
  exact — and fails the start when it exceeds a configurable ceiling.

## Considered options

- *`opentelemetry-api` as a fifth default dependency, as
  [`docs/research/04`](../research/04-modern-python-library-engineering-2026.md) §8 recommends* —
  rejected: the Core imports no third-party package
  ([ADR-0002](0002-core-scope-two-condition-test.md),
  [ADR-0032](0032-layer-model-and-direction-of-allowed-dependencies.md)), so the dependency would
  buy the Core nothing and only the Adapter and the plugins could use it — which is what an extra
  is for. It would also make this the only framework in the survey to do it, and it hard-codes one
  vendor's names for every user who runs neither backend.
- *Seams only, with a documented `opentelemetry-instrument` recipe and no first-party plugin*,
  the recommendation of
  [`docs/research/08`](../research/08-peer-responsibility-boundaries.md) for tracing — rejected:
  ADR-0026 promises a first-party observer as one of three deliberately supported levels of
  adoption, and a seam with no reference implementation is a record shape nobody has validated.
  Auto-instrumentation also cannot produce a dispatch span at all, and for HTTP it names spans by
  method alone because a generic transport cannot know the template.
- *Two components, one per library* — rejected: the label rules, the registry contract, the storage
  decorators and the snapshot reading would be stated twice.
- *A namespaced `aiommbot.*` metric vocabulary of our own* — rejected: it removes the risk that the
  Development-status messaging conventions rename something under us, at the price of no dashboard
  or alert from the ecosystem applying to us at all.
- *Defaulting the registry to the global one with an override* — rejected above; the friendlier
  one-liner is the one that breaks a second composition and a test suite.

## Consequences

- The messaging semantic conventions are **Development**, so the dispatch metric and span names
  follow a vocabulary that may change; the plugin's names are therefore **not** covered by this
  project's compatibility promise, and its documentation says so. The HTTP names are Stable and are
  covered.
- The plugin also ships an `HTTPTransport` decorator that injects `traceparent`, because
  propagation changes the call and modification is a decorator's job, never an observer's
  (ADR-0026).
- The cardinality Check has a setting, and a bot that legitimately exceeds the ceiling raises it
  deliberately instead of discovering the cost on a monitoring invoice.
