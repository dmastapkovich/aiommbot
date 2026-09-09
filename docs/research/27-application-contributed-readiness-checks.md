# 27. How an application contributes its own readiness checks

**Question.** When a framework ships liveness and readiness endpoints, how does it let the
application contribute its own checks? What shape does a contributed check take, how are liveness
and readiness kept apart, what runs a check and with what bound, and what does the response say?

Gathered for GitHub issue #95. [`docs/research/26`](26-schedule-reliability-and-probe-primitives.md)
§7 establishes what Kubernetes requires of a probe and what each Python peer exposes; it does not
record how an application *registers* a check, which is the whole design of a health mechanism.
Three axes are held throughout: **quality** — a liveness signal that cannot cascade, a readiness
signal that flips on shutdown, a check that throws not taking the endpoint down; **flexibility** —
the exact shape in which an application supplies a check and how much it can express; **efficiency**
— what stops a probe every ten seconds from becoming load on a dependency.

Findings only. Sources are primary — each project's own reference documentation and source at a
pinned branch or tag, the Kubernetes documentation, the gRPC health-checking specification, the ASGI
specification, RFC 9110 and 9112, and PyPI JSON metadata — read on 2026-09-09. Anything a primary
source did not confirm is marked **[unverified]**.

## 1 The two reference designs

### 1.1 Spring Boot Actuator: a bean is a contributor, a group is a probe

The contract is two interfaces. `HealthContributor` is a pure marker — in Spring Boot 4.x literally
`public sealed interface HealthContributor permits HealthIndicator, CompositeHealthContributor` with
no methods — and `HealthIndicator` is a `@FunctionalInterface` whose single method returns `Health`.
A `Health` carries exactly two fields, a `Status` and a `Map<String, Object>` of details; `Status`
has four constants (`UP`, `DOWN`, `OUT_OF_SERVICE`, `UNKNOWN`) and a public constructor, so custom
statuses are allowed and their severity comes from the list property
`management.endpoint.health.status.order`, defaulting to `[DOWN, OUT_OF_SERVICE, UP, UNKNOWN]`.

**The name is derived, not declared**: "The identifier for a given HealthIndicator is the name of
the bean without the HealthIndicator suffix, if it exists." There is no name, tag or group attribute
on the interface. Grouping happens outside the check, in configuration:
`management.endpoint.health.group.<name>.include` and `.exclude` list contributor ids and publish
`/actuator/health/<name>`, with `validate-group-membership` defaulting to `true` so a typo fails
start-up.

**The two probes are two groups.** `/actuator/health/liveness` and `/actuator/health/readiness` are
backed by `LivenessStateHealthIndicator` and `ReadinessStateHealthIndicator`, which read an
`ApplicationAvailability` abstraction rather than any dependency. `LivenessState` has two members,
`CORRECT` and `BROKEN`; `ReadinessState` has `ACCEPTING_TRAFFIC` and `REFUSING_TRAFFIC`. Both
default methods fail closed before any event is published — `getState(LivenessState.class,
LivenessState.BROKEN)` and `getState(ReadinessState.class, ReadinessState.REFUSING_TRAFFIC)`. Any
component can flip either by publishing an `AvailabilityChangeEvent`, and Spring publishes the
startup transitions itself: `LivenessState.CORRECT` after `ApplicationStartedEvent` and
`ReadinessState.ACCEPTING_TRAFFIC` after `ApplicationReadyEvent`.

**Nothing else is in the probe groups by default** — "By default, Spring Boot does not add other
health indicators to these groups" — so adding a dependency check to readiness is an explicit
opt-in, and the liveness group contains only the availability state.

Setting `management.endpoint.health.probes.add-additional-paths` to `true` publishes the liveness
group at **`/livez`** and the readiness group at **`/readyz`** on the main server port.

### 1.2 ASP.NET Core: a registration carries the name, the tags and the timeout

`IHealthCheck` declares one member, `Task<HealthCheckResult> CheckHealthAsync(HealthCheckContext
context, CancellationToken cancellationToken = default)`, and `HealthCheckContext` carries one
property — the `HealthCheckRegistration` — so a check learns its own name, tags, failure status and
timeout at run time. `HealthStatus` is a three-member enum whose numeric values encode severity:
`Unhealthy = 0`, `Degraded = 1`, `Healthy = 2`.

Registration is where the metadata lives: `AddCheck<T>(name, HealthStatus? failureStatus = null,
IEnumerable<string>? tags = null, TimeSpan? timeout = null)`, with a lambda overload that takes no
`failureStatus` because a lambda returns the status itself. **Tags exist for exactly one purpose,
filtering** — "A list of tags that can be used to filter health checks" — and there is no group,
hierarchy or ordering.

**The liveness/readiness split is a predicate over tags**, and the documented example is worth
copying verbatim: readiness is `app.MapHealthChecks("/healthz/ready", new HealthCheckOptions() {
Predicate = (check) => check.Tags.Contains("ready"), });` and liveness is
`app.MapHealthChecks("/healthz/live", new HealthCheckOptions() { Predicate = _ => false, });` The
docs state the consequence plainly: "The /healthz/live endpoint excludes all checks and reports a
Healthy status for all calls." A liveness endpoint is deliberately made **incapable of failing
because of a dependency** — and the aggregate of an empty set is documented as Healthy.

Two defaults are worth knowing because they are wrong for a probe. `HealthCheckRegistration.Timeout`
defaults to `Timeout.InfiniteTimeSpan`, so **a registered check has no time bound unless one is
passed**; and the timeout is cooperative, enforced with a linked `CancellationTokenSource`, so a
check that ignores its token is not actually stopped. `HealthCheckOptions.AllowCachingResponses`
defaults to `false` and the middleware then writes `Cache-Control: no-store, no-cache`, `Pragma:
no-cache` and an expired `Expires` — but that concerns HTTP caching only: the middleware calls
`CheckHealthAsync` on **every single request** and there is no result TTL on the pull path.

The push path is the efficiency answer. `IHealthCheckPublisher` runs the checks on a timer in a
hosted service and hands the `HealthReport` to every publisher, with `HealthCheckPublisherOptions`
defaulting to `Delay = 5s`, `Period = 30s`, `Timeout = 30s` and a null predicate; registrations are
grouped by their `(Delay, Period)` pair with one timer per group, so cheap and expensive checks can
run on different cadences.

## 2 Registration shapes, compared

| Project | State | Shape of a contributed check | Names | Grouping | Concurrent | Per-check timeout | Result cache |
|---|---|---|---|---|---|---|---|
| Spring Actuator | current | a bean implementing `HealthIndicator` | derived from the bean name | groups in configuration | **no — sequential** | **none**, only a 10 s slow warning | property, default `0ms` (off) |
| ASP.NET Core | current | `IHealthCheck` or a lambda, registered with name and tags | declared at registration | tags plus a predicate | yes | parameter, default **infinite** | none on the pull path; publisher on a timer |
| `fast-healthchecks` 1.2.0 | maintained | an object satisfying `async def __call__(self) -> HealthCheckResult` | attribute `name` or `_name` | named `Probe` objects | yes, `asyncio.gather` under a semaphore, cap 8 | per-check config, default 5.0 s | **none** |
| `django-health-check` 4.5.1 | maintained | a dataclass subclass of `HealthCheck` with `async def run(self)` | class name | one view per check list | yes, `asyncio.gather` | none generic | **never**, `@never_cache` |
| `litestar-saq` | maintained | not possible — the checks are fixed to the SAQ queues | — | — | — | — | — |
| `fastapi-health` 0.4.0 | stalled 2021 | a plain callable, possibly with `Depends` | — | — | via FastAPI's dependency system | none | none |
| `light-health` 1.0.1 | new, unproven | `registry.register_liveness(name, check)` / `register_readiness(...)` | declared | two registries | yes | **hard-coded 2.0 s** | none |
| `py-healthcheck` 1.10.1 | dead 2020 | `health.add_check(func)`, returning `(bool, str)` | — | — | no | `error_timeout`, default 0 (off) | `success_ttl=27`, `failed_ttl=9` |

Five distinct shapes exist across the ecosystem: a plain callable appended to an instance, a list of
callables passed to a factory, objects in a `checks=[...]` list on a probe or router, a factory
`.add(obj)` carrying an alias and tags, and a module-level registry. Only one — `fast-healthchecks`
— offers named probes, a per-check timeout, bounded concurrency and a partial-failure policy
together.

## 3 Liveness, readiness and shutdown

Three sources agree on the rule and one disagrees with itself.

**Kubernetes** defines `/livez` as the restart signal and `/readyz` as the traffic signal on its own
API server, and marks **`/healthz` deprecated since v1.16**; the same page documents per-check
sub-paths `/livez/<name>` and `/readyz/<name>` and an `?exclude=<name>` parameter, with verbose
lines of the form `[+]etcd ok`. Its probe reference states that a liveness probe must indicate only
an unrecoverable failure such as a deadlock, that an incorrect implementation "causes restarts under
high load, failed client requests, and increased load on the surviving pods", and that liveness
should generally reuse the readiness endpoint with a higher `failureThreshold` rather than run a
deeper check. It also warns the other way about readiness: a shared backend in a readiness probe
takes every instance out of service at once.

**Spring** implements the shutdown rule explicitly. Readiness flips to `REFUSING_TRAFFIC` in
`doClose()` *before* the web server is destroyed, so the probe reports not-ready while in-flight
requests still drain, and the documented lifecycle table keeps **liveness `CORRECT` throughout
graceful shutdown** — "The application is shutting down. Existing requests may still be processed
during the grace period. Readiness returns REFUSING_TRAFFIC to signal that the application is no
longer accepting new connections." Liveness only becomes `BROKEN` once shutdown is complete.

**Kubernetes does not need a readiness probe to drain a deletion.** The documented termination
sequence is: the API server records the deadline and the Pod shows as Terminating; the `preStop`
hook runs before SIGTERM; in parallel the control plane evaluates EndpointSlice removal; on
grace-period expiry the runtime sends SIGKILL. During termination an EndpointSlice endpoint carries
three conditions — `ready: false`, `serving: true`, `terminating: true` — and a load balancer that
wants to drain reads `serving`, not `ready`. The docs say directly that a readiness probe is not the
mechanism for draining on delete.

**For a Pod that no Service selects, readiness still matters** — just not for traffic. A failing
readiness probe removes the Pod from EndpointSlices, which is a null effect with no Service; but the
Pod `Ready` condition drives `minReadySeconds` (default 0), `rollingUpdate.maxUnavailable` and
`maxSurge` (both 25%), `progressDeadlineSeconds` (default 600), and PodDisruptionBudget, which
"defines healthy strictly as the Pod Ready condition". So readiness paces a rollout and protects
against voluntary eviction even for a WebSocket consumer with no listening port.

**ASP.NET Core has no shutdown-aware readiness at all** — the only documented mechanism is tag
filtering, and any shutdown behaviour must be written into an application-supplied check
**[unverified — a negative established across four source files]**. Neither does anything in the
Python set: **not one of Litestar, FastStream, `litestar-saq`, `fastapi-health`,
`fast-healthchecks`, `django-health-check` or `sanic-ext` flips readiness to failing on shutdown**;
`fast-healthchecks` has the only shutdown hook and it closes clients rather than failing readiness.

Two counter-examples show what happens without the rule. `cloudflared` names its endpoint `/ready`
and comments it "Intended for k8s readiness checks", and Cloudflare's own Kubernetes tutorial then
wires it as a **livenessProbe with `failureThreshold: 1`** — one failed dependency check restarts
the pod. FastStream's single `/health` is a broker ping with no separate liveness endpoint, so used
as liveness it is the same pattern.

## 4 What runs a check, and what happens when one misbehaves

**A check that throws must not take the endpoint down**, and the ecosystem learned this the hard
way. `django-health-check` 3.x re-raised anything that was not a `HealthCheckException` — `except
BaseException: logger.exception("Unexpected Error!"); raise` — so an exploding check produced an
unhandled 500; 4.x catches `BaseException`, logs it and substitutes one failed entry.
`fast-healthchecks` re-raises only `asyncio.CancelledError`, `SystemExit` and `KeyboardInterrupt`
and converts every other exception into a failed result. ASP.NET Core catches everything except
`OperationCanceledException` — deliberately, so a client-aborted request propagates rather than
being recorded as a failed check — and converts it to the registration's failure status with the
exception's message as the description. Spring is the outlier: safety comes from *extending*
`AbstractHealthIndicator`, whose `final health()` wraps the subclass call in `try/catch`; a bare
`HealthIndicator` bean that throws propagates out of the endpoint.

**Bounding a slow check is where the references are weakest.** Spring has no per-indicator timeout
at all; its only timing feature is `management.endpoint.health.logging.slow-indicator-threshold`,
default 10 s, which logs "Health contributor %s took %s to respond" from a `finally` block *after*
the call completed and never interrupts it. ASP.NET Core has a per-check timeout that defaults to
infinite. `fast-healthchecks` sets 5.0 s per check and `light-health` hard-codes 2.0 s. This matters
against the kubelet, whose `timeoutSeconds` defaults to **1** and which treats an exceeded timeout
as a plain Failure — there is no degraded outcome, only Success, Failure and Unknown.

**Concurrency splits the field.** Spring runs contributors sequentially, with no parallel stream or
executor, so endpoint latency is the sum of contributor latencies. `django-health-check` 4.x and
`fast-healthchecks` both use `asyncio.gather`, the latter capped by an `asyncio.Semaphore` at
`DEFAULT_MAX_CONCURRENCY = 8`. Both dispatch a synchronous check to an executor —
`fast-healthchecks` documents the trap in its own source: "A timeout abandons the worker thread
rather than cancelling it", so the blocking call keeps running after the check has failed.

**Result caching barely exists.** Spring offers `management.endpoint.health.cache.time-to-live` and
defaults it to `0ms`. `fast-healthchecks` caches *clients*, not results, and a repository-wide
search for a TTL returns nothing. `django-health-check` never caches, wraps its view in
`@never_cache`, and its own documentation calls the endpoint a denial-of-service vector whose
mitigation is a secret URL segment. The only result cache in the set is the dead Runscope lineage,
with `success_ttl=27` and `failed_ttl=9` seconds. **A probe every ten seconds re-running every
dependency check is therefore the ecosystem's normal behaviour, not a considered one** — the two
mechanisms that avoid it are ASP.NET Core's timer-driven publisher and `arq`'s Redis key with its
TTL ([`docs/research/26`](26-schedule-reliability-and-probe-primitives.md) §7.3).

## 5 What the response says, and what it must not

Kubernetes reads the status code and nothing else: success is any code from 200 to 399, the body is
not parsed, and the kubelet stops reading after 10 KiB. The implementations converge on an empty
body: FastStream pre-allocates `AsgiResponse(b"", 204)` and `AsgiResponse(b"", 500)`;
`fast-healthchecks` defaults to `204` healthy and `503` unhealthy and suppresses the body for
statuses that cannot carry one. RFC 9112 §6.3 is the reason — a 204 response "is always terminated
by the first empty line after the header fields … and thus cannot contain a message body". RFC 9110
adds that a 503 "MAY send a Retry-After header field"; none of the four Python implementations
examined does.

Detail exposure is treated as a security concern by the two most mature designs. Spring defaults
`management.endpoint.health.show-details` to `never` and gates the other values on authorization
roles. `django-health-check` 4.x warns that a check's `__repr__` is used verbatim in the report and
instructs authors to set `repr=False` on sensitive dataclass fields and to keep secrets out of
exception messages; `fast-healthchecks` redacts secrets in error metadata automatically and warns
that its `debug=True` output "may name internal hosts or dependency details".

## 6 The one real standard is not HTTP

The gRPC Health Checking Protocol is a versioned protobuf contract: `service Health { rpc
Check(HealthCheckRequest) returns (HealthCheckResponse); rpc Watch(HealthCheckRequest) returns
(stream HealthCheckResponse); }`, a request of one `string service` field, and a four-member
`ServingStatus` enum — `UNKNOWN`, `SERVING`, `NOT_SERVING`, `SERVICE_UNKNOWN`. An empty service name
is the reserved key for the whole server. `Check` fails with `NOT_FOUND` for an unknown service
while `Watch` answers `SERVICE_UNKNOWN` and keeps the stream open; `Watch` sends the current status
immediately and then only on change, which is the protocol's answer to per-probe polling cost.
Shutdown is a named reason for `NOT_SERVING`: "A server may choose to reply 'unhealthy' because it
is not ready to take requests, it is shutting down or some other reason." The client is told to set
its own deadline; there is no server-side per-check timeout in the protocol.

Kubernetes consumes it natively — alpha in v1.23, beta in v1.24, **stable in v1.27** — with a
`GRPCAction` of `port` and optional `service`, and documents that "All errors are considered as
probe failures", so nothing but `SERVING` passes. `grpc-health-probe` still exists for older
clusters and now defers to the built-in capability in its own README.

Nothing equivalent exists over HTTP. ASP.NET Core's own default body is the bare word `Healthy`,
`Degraded` or `Unhealthy` at a path and a status mapping the application chooses; the only IETF
attempt at a response format expired in 2022
([`docs/research/26`](26-schedule-reliability-and-probe-primitives.md) §7.2).

## 7 What is alive in Python

Only two packages have 2026 activity: `django-health-check` 4.5.1 (released 2026-08-21, pushed
2026-09-08, Django-only) and `fast-healthchecks` 1.2.0 (released 2026-08-26, pushed 2026-09-04, ASGI
and framework-agnostic — but 27 stars, and its documented Litestar example is missing from the
repository). Everything else last released between 2016 and 2024: the original Runscope
`healthcheck` is dead and its repository returns 404, `py-healthcheck` still depends on `six`,
`aiohttp-healthcheck` still imports `imp` and decorates with `@asyncio.coroutine` and therefore
cannot even import on a supported Python, `fastapi-healthcheck` is archived, `fastapi-health`'s
richer API exists only unreleased on `main`, and `fastapi-healthchecks` has no findable source
repository. `light-health` (2025-12-25, one release, zero stars) is the only other ASGI-native
candidate.

**Litestar ships nothing.** A repository-wide search for readiness, liveness or probe returns
nothing, and the only health-shaped code is a hand-written route in a testing example. What Litestar
does provide is the reference for *how a plugin contributes a route*: `InitPlugin.on_app_init(self,
app_config: AppConfig) -> AppConfig` mutates an `AppConfig` dataclass in place, and its own
docstring example appends to `app_config.route_handlers` and writes into `app_config.dependencies`.
Plugins are applied in registration order. Registering a route after the application exists emits a
warning that it "is discouraged … and is a costly operation". `litestar-saq` is the one
Litestar-ecosystem plugin that does ship an HTTP health route — and its checks are fixed to the SAQ
queues, its failure status is 500 rather than 503, and an application cannot contribute anything to
it.

FastStream's `make_ping_asgi(broker, /, timeout=None, ...)` has **no hook by which an application
extends what it checks**: the generated handler's whole body is `if await broker.ping(timeout):
return healthy_response; return unhealthy_response`. An application adds its *own* route instead,
through `AsgiFastStream(..., asgi_routes=...)` or `mount(path, route)`; dispatch is exact string
equality on `scope["path"]` with no prefix tolerance. Its ASGI type aliases are plain
`MutableMapping` and `Callable` with no Starlette dependency, and `AsgiResponse` is about forty
lines.

For a bare ASGI application the specification is short: an application is "a single async callable:
coroutine application(scope, receive, send)"; the HTTP scope keys a two-path health app needs are
`type`, `method` and `path`; and a response is exactly two messages, `http.response.start` with
`status` and optional `headers`, then `http.response.body`, with the start message required to come
first.

## 8 What the evidence supports

- **A check is an object with a name and its own bound**, supplied by the application and never
  discovered. Spring derives the name from a bean and pays for it with a magic suffix rule; ASP.NET
  Core and `fast-healthchecks` both put the name, the timeout and the grouping on the registration,
  which is the shape that survives. - **Liveness runs no check.** The strongest form in the field is
  ASP.NET Core's `Predicate => false` and Spring's liveness group containing only an availability
  state — an endpoint that cannot fail because of a dependency. Kubernetes says the same in prose. -
  **Readiness flips on shutdown; liveness does not.** Spring is the only project examined that
  implements it, and it keeps liveness `CORRECT` for the whole grace period so the platform does not
  kill a draining instance. No Python project does either half. - **A throwing check is one failed
  check.** Two of the maintained implementations get this right and one of them only after shipping
  the opposite; Spring still requires the author to inherit from the right base class to be safe. -
  **A per-check bound and bounded concurrency are the parts most implementations lack**, and the
  kubelet's one-second default timeout is what makes them matter. - **A result cache is missing
  everywhere and is the obvious remaining lever**: the pull model re-runs every dependency check on
  every probe, which `django-health-check` documents as a denial-of-service surface. - **The body is
  not a contract; the status code is.** Kubernetes parses no body, an empty 204 is the convergent
  answer, and both mature designs treat details as an information-disclosure decision that defaults
  to hiding them. - **`/livez` and `/readyz` are the authoritative names**, from the Kubernetes API
  server's own health endpoints, where `/healthz` has been deprecated since v1.16 and Spring
  publishes exactly those two paths.

## Sources

Spring Boot Actuator:

- <https://docs.spring.io/spring-boot/reference/actuator/endpoints.html> · <https://docs.spring.io/spring-boot/appendix/application-properties/index.html>
- <https://raw.githubusercontent.com/spring-projects/spring-boot/main/module/spring-boot-health/src/main/java/org/springframework/boot/health/contributor/HealthContributor.java> · <https://raw.githubusercontent.com/spring-projects/spring-boot/main/module/spring-boot-health/src/main/java/org/springframework/boot/health/contributor/HealthIndicator.java> · <https://raw.githubusercontent.com/spring-projects/spring-boot/main/module/spring-boot-health/src/main/java/org/springframework/boot/health/contributor/CompositeHealthContributor.java>
- <https://raw.githubusercontent.com/spring-projects/spring-boot/3.5.x/spring-boot-project/spring-boot-actuator/src/main/java/org/springframework/boot/actuate/health/HealthIndicator.java> · <https://raw.githubusercontent.com/spring-projects/spring-boot/3.5.x/spring-boot-project/spring-boot-actuator/src/main/java/org/springframework/boot/actuate/health/Health.java> · <https://raw.githubusercontent.com/spring-projects/spring-boot/3.5.x/spring-boot-project/spring-boot-actuator/src/main/java/org/springframework/boot/actuate/health/Status.java>
- <https://raw.githubusercontent.com/spring-projects/spring-boot/3.5.x/spring-boot-project/spring-boot/src/main/java/org/springframework/boot/availability/LivenessState.java> · <https://raw.githubusercontent.com/spring-projects/spring-boot/3.5.x/spring-boot-project/spring-boot/src/main/java/org/springframework/boot/availability/ReadinessState.java> · <https://raw.githubusercontent.com/spring-projects/spring-boot/3.5.x/spring-boot-project/spring-boot-actuator/src/main/java/org/springframework/boot/actuate/availability/ReadinessStateHealthIndicator.java>
- <https://raw.githubusercontent.com/spring-projects/spring-boot/3.5.x/spring-boot-project/spring-boot-actuator/src/main/java/org/springframework/boot/actuate/endpoint/invoker/cache/CachingOperationInvoker.java>

ASP.NET Core:

- <https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/health-checks?view=aspnetcore-9.0> · <https://raw.githubusercontent.com/dotnet/AspNetCore.Docs/main/aspnetcore/host-and-deploy/health-checks.md>
- <https://raw.githubusercontent.com/dotnet/aspnetcore/main/src/HealthChecks/Abstractions/src/IHealthCheck.cs> · <https://raw.githubusercontent.com/dotnet/aspnetcore/main/src/HealthChecks/Abstractions/src/HealthStatus.cs> · <https://raw.githubusercontent.com/dotnet/aspnetcore/main/src/HealthChecks/Abstractions/src/HealthCheckResult.cs> · <https://raw.githubusercontent.com/dotnet/aspnetcore/main/src/HealthChecks/Abstractions/src/HealthCheckRegistration.cs>
- <https://raw.githubusercontent.com/dotnet/aspnetcore/main/src/HealthChecks/HealthChecks/src/DefaultHealthCheckService.cs> · <https://raw.githubusercontent.com/dotnet/aspnetcore/main/src/HealthChecks/HealthChecks/src/HealthCheckPublisherOptions.cs> · <https://raw.githubusercontent.com/dotnet/aspnetcore/main/src/HealthChecks/HealthChecks/src/HealthCheckPublisherHostedService.cs> · <https://raw.githubusercontent.com/dotnet/aspnetcore/main/src/Middleware/HealthChecks/src/HealthCheckMiddleware.cs> · <https://raw.githubusercontent.com/dotnet/aspnetcore/main/src/Middleware/HealthChecks/src/HealthCheckResponseWriters.cs>

Kubernetes and gRPC:

- <https://kubernetes.io/docs/reference/using-api/health-checks/> · <https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/> · <https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination> · <https://kubernetes.io/docs/tutorials/services/pods-and-endpoint-termination-flow/> · <https://kubernetes.io/blog/2022/05/13/grpc-probes-now-in-beta/>
- <https://raw.githubusercontent.com/grpc/grpc/master/doc/health-checking.md> · <https://raw.githubusercontent.com/grpc/grpc/master/src/proto/grpc/health/v1/health.proto> · <https://grpc.io/docs/guides/health-checking/> · <https://raw.githubusercontent.com/grpc-ecosystem/grpc-health-probe/master/README.md>
- <https://www.rfc-editor.org/rfc/rfc9110.html#name-503-service-unavailable> · <https://www.rfc-editor.org/rfc/rfc9112.html>

ASGI and the Python ecosystem:

- <https://asgi.readthedocs.io/en/latest/specs/main.html> · <https://asgi.readthedocs.io/en/latest/specs/www.html>
- <https://github.com/litestar-org/litestar/blob/main/litestar/plugins/base.py> · <https://github.com/litestar-org/litestar/blob/main/litestar/config/app.py> · <https://docs.litestar.dev/latest/usage/plugins/index.html> · <https://github.com/litestar-org/litestar-saq/blob/main/litestar_saq/controllers.py> · <https://github.com/litestar-org/advanced-alchemy/blob/main/advanced_alchemy/repository/_async.py>
- <https://github.com/ag2ai/faststream/blob/main/faststream/asgi/factories/ping.py> · <https://github.com/ag2ai/faststream/blob/main/faststream/asgi/app.py> · <https://github.com/ag2ai/faststream/blob/main/faststream/asgi/handlers.py> · <https://github.com/ag2ai/faststream/blob/main/faststream/asgi/response.py> · <https://github.com/ag2ai/faststream/blob/main/faststream/asgi/types.py>
- <https://pypi.org/pypi/django-health-check/4.5.1/json> · <https://github.com/codingjoe/django-health-check/blob/main/health_check/base.py> · <https://github.com/codingjoe/django-health-check/blob/main/health_check/views.py> · <https://github.com/codingjoe/django-health-check/blob/main/docs/migrate-to-v4.md> · <https://github.com/codingjoe/django-health-check/blob/3.20.5/health_check/backends.py>
- <https://pypi.org/pypi/fast-healthchecks/json> · <https://github.com/ZYLVEXT/fast-healthchecks/blob/main/fast_healthchecks/execution.py> · <https://github.com/ZYLVEXT/fast-healthchecks/blob/main/fast_healthchecks/checks/_base.py> · <https://github.com/ZYLVEXT/fast-healthchecks/blob/main/fast_healthchecks/integrations/base.py> · <https://github.com/ZYLVEXT/fast-healthchecks/blob/main/fast_healthchecks/checks/function.py> · <https://github.com/ZYLVEXT/fast-healthchecks/blob/main/docs/probe-options.md>
- <https://pypi.org/pypi/fastapi-health/json> · <https://github.com/Kludex/fastapi-health/blob/main/fastapi_health/route.py> · <https://pypi.org/pypi/fastapi-healthchecks/1.1.0/json> · <https://pypi.org/pypi/healthcheck/json> · <https://github.com/ateliedocodigo/py-healthcheck/blob/develop/healthcheck/healthcheck.py> · <https://github.com/brannon/aiohttp-healthcheck/blob/master/aiohttp_healthcheck/__init__.py> · <https://pypi.org/pypi/light-health/json> · <https://github.com/tiagoBarbano/light-health/blob/master/src/light_health/registry.py>
- <https://github.com/sanic-org/sanic-ext/blob/main/sanic_ext/extensions/health/endpoint.py> · <https://github.com/stephenhillier/starlette_exporter/blob/master/README.md>
