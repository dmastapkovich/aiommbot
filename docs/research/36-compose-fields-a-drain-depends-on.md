# 30. The Docker Compose fields a graceful drain depends on

**Question.** Which Docker Compose fields does a graceful drain depend on, what does Compose offer
in place of a liveness and a readiness probe, and can it bound a workload to one live instance?
[ADR-0023](../adr/0023-websocket-gateway-resilience.md) drains for at most 25 s, and
[ADR-0063](../adr/0063-the-process-declares-its-shutdown-budget-and-the-bot-bounds-the-stop.md)
makes the host's budget a declared field, so the number Compose gives by default decides whether a
bot stops correctly on it.

Gathered for GitHub issue #99, beside
[`docs/research/29`](29-kubernetes-fields-a-drain-depends-on.md), which asks the same questions of
Kubernetes. The two hosts answer them the other way round from each other, which is the finding.

Findings only. Sources are primary — the `compose-spec/compose-spec` specification and its JSON
schema, `docs.docker.com`, and the upstream Dockerfile reference in `moby/buildkit` — read on
2026-09-10. Where the specification repository and the published reference differ, both are quoted
and the difference is named. Anything a primary source did not confirm is marked **[unverified]**.

The deployment view carries one subsection per host, and the second is Docker Compose. Its
defaults run the other way from Kubernetes', which is the finding: the budget is shorter than the
drain rather than longer than it.

## 1 The stop sequence and its budget

### 1.1 `stop_grace_period`

The Compose specification defines the whole stop budget in one attribute
([05-services.md](https://raw.githubusercontent.com/compose-spec/compose-spec/main/05-services.md)):

> `stop_grace_period` specifies how long Compose must wait when attempting to stop a container if
> it doesn't handle SIGTERM (or whichever stop signal has been specified with `stop_signal`),
> before sending SIGKILL. It's specified as a duration.

and, in the same section:

> Default value is 10 seconds for the container to exit before sending SIGKILL.

Accepted forms are durations, illustrated in the specification as `stop_grace_period: 1s` and
`stop_grace_period: 1m30s`. The published Compose file reference carries the same two sentences
verbatim
([docs.docker.com](https://docs.docker.com/reference/compose-file/services/)). The two sources
agree.

**The default is 10 s. That is shorter than a 25 s drain.**

### 1.2 `stop_signal`

> `stop_signal` defines the signal that Compose uses to stop the service containers. If unset
> containers are stopped by Compose by sending `SIGTERM`.

([05-services.md](https://raw.githubusercontent.com/compose-spec/compose-spec/main/05-services.md);
identical on
[docs.docker.com](https://docs.docker.com/reference/compose-file/services/).) The example given is
`stop_signal: SIGUSR1`.

### 1.3 The documented order

The specification states the order only inside the `stop_grace_period` sentence quoted above:
Compose sends the stop signal, waits `stop_grace_period`, then sends SIGKILL. The Docker CLI
reference for `docker stop` states it as its own sentence
([docs.docker.com](https://docs.docker.com/reference/cli/docker/container/stop/)):

> The main process inside the container will receive `SIGTERM`, and after a grace period, `SIGKILL`.

SIGKILL is not catchable, so the grace period is a hard ceiling on drain time, not a target.

### 1.4 CLI timeouts

| Command | Flag | Documented default | Documented description |
| --- | --- | --- | --- |
| `docker stop` | `-t`, `--timeout` | see below | "Seconds to wait before killing the container" |
| `docker compose down` | `-t`, `--timeout` | empty cell | "Specify a shutdown timeout in seconds" |
| `docker compose stop` | `-t`, `--timeout` | empty cell | "Specify a shutdown timeout in seconds" |
| `docker compose up` | `-t`, `--timeout` | empty cell | "Use this timeout in seconds for container shutdown when attached or when containers are already running" |

For `docker stop` the reference states
([docs.docker.com](https://docs.docker.com/reference/cli/docker/container/stop/)):

> the Daemon determines the default, and is 10 seconds for Linux containers, and 30 seconds for
> Windows containers.

For the three `docker compose` subcommands the Default column of the options table is empty
([down](https://docs.docker.com/reference/cli/docker/compose/down/),
[stop](https://docs.docker.com/reference/cli/docker/compose/stop/),
[up](https://docs.docker.com/reference/cli/docker/compose/up/)). No default is printed there, and
the effective value falls back to the service's `stop_grace_period`, whose own default is 10 s.
**[unverified]** — no page on `docs.docker.com` was found that states the fallback rule in words;
the `down`, `stop` and `up` CLI references were each read in full and none contains a sentence
tying `--timeout` to `stop_grace_period`.

The practical consequence is that a CLI flag can shorten the budget below whatever the Compose file
declares. `docker compose down -t 5` kills after 5 s regardless of a 30 s `stop_grace_period`.

### 1.5 What an operator observes when the budget is too short

At the grace deadline the container receives SIGKILL, and the process exits with no further
opportunity to run code. The container's exit code is 137 (128 + SIGKILL). Compose reports the
container as exited. There is no log line saying "grace period exceeded" — the process simply stops
mid-drain, and any work it had not finished is lost. **[unverified]** — the 137 exit code is not
stated on any of the Compose or CLI reference pages read here; the `docker stop` reference documents
only the SIGTERM-then-SIGKILL sequence.

## 2 Is there anything corresponding to `preStop`?

**Yes.** Unlike the premise of the question, the Compose specification does define pre-stop
lifecycle hooks, alongside `pre_start` and `post_start`.

The specification repository says
([05-services.md](https://raw.githubusercontent.com/compose-spec/compose-spec/main/05-services.md)):

> `pre_stop` defines a sequence of lifecycle hooks to run before service termination.
>
> Configuration is equivalent to `post_start`.

`post_start`, whose configuration `pre_stop` inherits, is defined as:

> `post_start` defines a sequence of lifecycle hooks to run after a container has started. The exact
> timing of when the command is run is not guaranteed.

with the attributes `command` ("The command to run after the container has started. This attribute
is required."), `user`, `privileged`, `working_dir` and `environment`.

**The specification and the docs site differ here, and the difference is material.** The published
reference adds a caveat the specification repository omits
([docs.docker.com](https://docs.docker.com/reference/compose-file/services/)):

> `pre_stop` ... Defines a sequence of lifecycle hooks to run before the container is stopped. These
> hooks won't run if the container stops by itself or is terminated suddenly.

So a `pre_stop` hook is not a reliable shutdown path. It runs on an operator-initiated stop and not
when the process exits on its own or is killed. It is also a command executed in the container, not
a signal to the running process, so it does not extend the drain the process itself performs.

The specification does not state whether `pre_stop` runs inside or outside the `stop_grace_period`
budget. **[unverified]** — both the `pre_stop` sections read above were checked for any mention of
`stop_grace_period` and neither mentions it.

## 3 What Compose has instead of probes

### 3.1 The `healthcheck` key

The specification anchors the semantics to the image instruction
([05-services.md](https://raw.githubusercontent.com/compose-spec/compose-spec/main/05-services.md)):

> `healthcheck` declares a check that's run to determine whether or not the service containers are
> "healthy". It works in the same way, and has the same default values, as the HEALTHCHECK
> Dockerfile instruction set by the service's Docker image. Your Compose file can override the
> values set in the Dockerfile.

The specification's own example, copied verbatim:

```yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost"]
  interval: 1m30s
  timeout: 10s
  retries: 3
  start_period: 40s
  start_interval: 5s
```

The prose section documents `test` and `disable` but does not describe `interval`, `timeout`,
`retries`, `start_period` or `start_interval` individually beyond noting that `interval`, `timeout`,
`start_period` and `start_interval` are "specified as durations". The per-field descriptions and
defaults live in the JSON schema
([schema/compose-spec.json](https://raw.githubusercontent.com/compose-spec/compose-spec/main/schema/compose-spec.json)):

| Field | Schema description (verbatim) | Default |
| --- | --- | --- |
| `test` | "The test to perform to check container health. Can be a string or a list. The first item is either NONE, CMD, or CMD-SHELL. If it's CMD, the rest of the command is exec'd. If it's CMD-SHELL, the rest is run in the shell." | none |
| `interval` | "Time between running the check (e.g., '1s', '1m30s'). Default: 30s." | 30s |
| `timeout` | "Maximum time to allow one check to run (e.g., '1s', '1m30s'). Default: 30s." | 30s |
| `retries` | "Number of consecutive failures needed to consider the container as unhealthy. Default: 3." | 3 |
| `start_period` | "Start period for the container to initialize before starting health-retries countdown (e.g., '1s', '1m30s'). Default: 0s." | 0s |
| `start_interval` | "Time between running the check during the start period (e.g., '1s', '1m30s'). Default: interval value." | see note |
| `disable` | "Disable any container-specified healthcheck. Set to true to disable." | false |

The Dockerfile reference gives the same defaults for four of the five timing options —
`--interval=30s`, `--timeout=30s`, `--start-period=0s`, `--retries=3` — but states
`--start-interval=5s`
([docs.docker.com](https://docs.docker.com/reference/dockerfile/#healthcheck), corroborated by the
upstream source of that page,
[moby/buildkit reference.md](https://raw.githubusercontent.com/moby/buildkit/master/frontend/dockerfile/docs/reference.md)).

**This is a genuine divergence.** The Compose schema says `start_interval` defaults to the
`interval` value; the Dockerfile reference says 5 s. The Compose prose claims the two have "the same
default values", which contradicts the Compose schema itself. Set `start_interval` explicitly rather
than relying on either.

The specification's prose for `test`:

> `test` defines the command Compose runs to check container health. It can be either a string or a
> list. If it's a list, the first item must be either `NONE`, `CMD` or `CMD-SHELL`. If it's a
> string, it's equivalent to specifying `CMD-SHELL` followed by that string.

> Using `CMD-SHELL` runs the command configured as a string using the container's default shell
> (`/bin/sh` for Linux).

> `NONE` disables the healthcheck, and is mostly useful to disable the Healthcheck Dockerfile
> instruction set by the service's Docker image.

The Dockerfile reference defines the exit-code contract: "0 means success — the container is healthy
and ready for use", "1 means unhealthy — the container is not working correctly", "2 is reserved; do
not use this exit code"
([moby/buildkit reference.md](https://raw.githubusercontent.com/moby/buildkit/master/frontend/dockerfile/docs/reference.md)).
Health status is one of `starting`, `healthy` or `unhealthy`.

### 3.2 Does anything restart or kill a container because its health check fails?

**No.** Nothing in the Compose specification or the Docker restart-policy documentation acts on
health status.

The restart attribute is scoped to termination, not health
([05-services.md](https://raw.githubusercontent.com/compose-spec/compose-spec/main/05-services.md)):

> `restart` defines the policy that the platform applies on container termination.

Docker's own restart-policy page is scoped the same way
([docs.docker.com](https://docs.docker.com/engine/containers/start-containers-automatically/)):

> Docker provides restart policies to control whether your containers start automatically when they
> exit, or when Docker restarts.

An unhealthy container has not exited, so no restart policy value can reach it. The same holds for
`deploy.restart_policy`, whose `condition` values are `none`, `on-failure` and `any` — all defined
against exit status
([deploy.md](https://raw.githubusercontent.com/compose-spec/compose-spec/main/deploy.md)).

The negative is established by a search of the specification's JSON schema
([schema/compose-spec.json](https://raw.githubusercontent.com/compose-spec/compose-spec/main/schema/compose-spec.json))
for every property name containing `health`. It returns exactly eight: `healthcheck` on the service
object, and `disable`, `interval`, `retries`, `test`, `timeout`, `start_period` and `start_interval`
inside it. None of them names an action. There is no `on_unhealthy`, no `unhealthy_action`, no
restart-on-unhealthy key anywhere in the schema.

Whether Swarm mode behaves differently is **[unverified]** — no Swarm reference page was read for
this note; the claim was seen only in secondary search results and is not repeated here as fact.

### 3.3 What actually consumes the health state

Three consumers are documented.

1. **`depends_on` with `condition: service_healthy`.** The specification says
   ([05-services.md](https://raw.githubusercontent.com/compose-spec/compose-spec/main/05-services.md)):

   > `service_healthy`: Specifies that a dependency is expected to be "healthy" (as indicated by
   > healthcheck) before starting a dependent service.

   The Compose how-to restates it
   ([docs.docker.com](https://docs.docker.com/compose/how-tos/startup-order/)):

   > Compose waits for healthchecks to pass on dependencies marked with `service_healthy`.

   This gate is one-shot: it applies at startup, before the dependent service is created. Nothing
   re-evaluates it while the stack runs.

2. **`docker compose up --wait`.** The options table reads
   ([docs.docker.com](https://docs.docker.com/reference/cli/docker/compose/up/)):

   > `--wait` — Wait for services to be running|healthy. Implies detached mode.

   with a companion flag:

   > `--wait-timeout` — Maximum duration in seconds to wait for the project to be running|healthy

   Neither flag has a documented default in the Default column.

3. **`pre_start` steps, indirectly.** The specification states
   ([05-services.md](https://raw.githubusercontent.com/compose-spec/compose-spec/main/05-services.md)):

   > `pre_start` steps only run once the service's `depends_on` conditions have been satisfied, so a
   > step can rely on those dependencies the same way the main service command does.

That is the whole list. Health state is read at startup and reported; it drives nothing at steady
state.

### 3.4 Does Compose distinguish liveness from readiness?

**No.** There is exactly one health axis.

The negative is established by the same schema search
([schema/compose-spec.json](https://raw.githubusercontent.com/compose-spec/compose-spec/main/schema/compose-spec.json)):
searching every property name for the substrings `live`, `ready` and `probe` returns nothing for all
three. There is no liveness key, no readiness key and no probe key in the specification.

The docs site says the same thing from the other direction
([docs.docker.com](https://docs.docker.com/compose/how-tos/startup-order/)):

> On startup, Compose does not wait until a container is "ready", only until it's running.

`healthcheck` plus `depends_on: condition: service_healthy` is how you recover a readiness gate, and
it is a startup gate only. Nothing in Compose corresponds to a liveness probe, because nothing acts
on a failing check (§C.2).

### 3.5 A health check is always a command inside the container

`test` accepts a string or a list whose first item is `NONE`, `CMD` or `CMD-SHELL`
([05-services.md](https://raw.githubusercontent.com/compose-spec/compose-spec/main/05-services.md)).
`CMD` execs the rest; `CMD-SHELL` runs the rest through the container's default shell; a bare string
is shorthand for `CMD-SHELL`. There is no HTTP form, no TCP form and no gRPC form. The schema
confirms it: the `test` property is typed as a string or an array of strings, with no alternative
object shape
([schema/compose-spec.json](https://raw.githubusercontent.com/compose-spec/compose-spec/main/schema/compose-spec.json)).

The consequence for a process whose only health surface is an ASGI endpoint: the check has to be
performed from inside the container by a program the image ships. The specification's own example
assumes `curl` is installed:

```yml
test: ["CMD", "curl", "-f", "http://localhost"]
```

A slim Python image typically has neither `curl` nor `wget`. The interpreter is always there, so the
check can be a Python one-liner against the local probe endpoint instead of an added binary. Either
way the HTTP request originates inside the container — Compose never makes one on the service's
behalf, which is the concrete difference from a Kubernetes `httpGet` probe.

## 4 Replicas and a singleton

### 4.1 `deploy.replicas`

The specification says
([deploy.md](https://raw.githubusercontent.com/compose-spec/compose-spec/main/deploy.md)):

> If the service is `replicated` (which is the default), `replicas` specifies the number of
> containers that should be running at any given time.

and for `mode`:

> `mode` defines the replication model used to run the service on the platform. Either `global`,
> exactly one container per physical node, or `replicated`, a specified number of containers. The
> default is `replicated`.

Note that `global` guarantees one container *per node*, not one container overall.

### 4.2 Whether `deploy` is honoured by `docker compose`

**The specification does not say `deploy` is ignored.** It frames it as optional and
platform-directed
([deploy.md](https://raw.githubusercontent.com/compose-spec/compose-spec/main/deploy.md)):

> Deploy is an optional part of the Compose Specification. The Compose Deploy Specification lets you
> declare additional metadata on services so Compose gets relevant data to allocate adequate
> resources on the platform and configure them to match your needs.

The negative is established by a targeted read of `deploy.md` front to back, asking for any sentence
containing "ignore", "not supported", "Swarm", "orchestrator" or "platform-specific exclusion": none
of those sentences exists. The published deploy page carries the same framing with no such
disclaimer either
([docs.docker.com](https://docs.docker.com/reference/compose-file/deploy/)). Which sub-keys
`docker compose` honours in practice is not stated on either page. **[unverified]** — both the
specification's `deploy.md` and the published deploy reference were read in full and neither
enumerates honoured versus ignored sub-keys.

### 4.3 `scale` and `--scale`

The service-level `scale` attribute
([05-services.md](https://raw.githubusercontent.com/compose-spec/compose-spec/main/05-services.md)):

> `scale` specifies the default number of containers to deploy for this service. When both are set,
> `scale` must be consistent with the `replicas` attribute in the Deploy Specification.

The CLI flag ([docs.docker.com](https://docs.docker.com/reference/cli/docker/compose/up/)):

> `--scale` — Scale SERVICE to NUM instances. Overrides the `scale` setting in the Compose file if
> present.

The flag's documented target is the `scale` setting, not `deploy.replicas`. Since the specification
requires the two to be consistent when both are set, the flag effectively overrides the declared
count, but the documentation only names `scale`.

### 4.4 Is there any at-most-one guarantee?

**No.** Compose offers no lease, no lock, no leader election and no fencing token.

The negative is established by the schema search
([schema/compose-spec.json](https://raw.githubusercontent.com/compose-spec/compose-spec/main/schema/compose-spec.json)):
property names containing `replica` return only `replicas` on the deployment object; property names
containing `scale` return only `scale` on the service object. No key expresses exclusivity,
singleton semantics or a distributed lock.

The closest documented mechanism is the update ordering, and it lives in the deploy section
([deploy.md](https://raw.githubusercontent.com/compose-spec/compose-spec/main/deploy.md)):

> `order`: Order of operations during updates. One of `stop-first` (old task is stopped before
> starting new one), or `start-first` (new task is started first, and the running tasks briefly
> overlap) (default `stop-first`).

The same wording appears for `rollback_config.order`. `stop-first` is the default and does describe
non-overlapping instances during an update, but it is phrased in terms of Swarm "tasks" and it
governs a rolling update, not the general recreate path. Whether `docker compose up` on a changed
service stops the old container before starting the new one is **[unverified]** — the `up` CLI
reference was read and states no ordering for recreation.

If exactly one live instance matters, it has to be enforced by the application — a lock in the
datastore the bot already uses — not by Compose.

## 5 `restart` policies

### 5.1 The four values

The specification
([05-services.md](https://raw.githubusercontent.com/compose-spec/compose-spec/main/05-services.md)):

> `restart` defines the policy that the platform applies on container termination.
>
> - `no`: The default restart policy. It does not restart the container under any circumstances.
> - `always`: The policy always restarts the container until its removal.
> - `on-failure[:max-retries]`: The policy restarts the container if the exit code indicates an
>   error. Optionally, limit the number of restart retries the container runtime attempts.
> - `unless-stopped`: The policy restarts the container irrespective of the exit code but stops
>   restarting when the service is stopped or removed.

The accepted literals, from the specification's example block: `restart: "no"`, `restart: always`,
`restart: on-failure`, `restart: on-failure:3`, `restart: unless-stopped`. **`on-failure:<n>` exists
and is spelled with a colon.**

**The default is `no`** — the specification states it inside the `no` bullet itself.

The Docker engine page gives the same four with slightly different wording and adds two operational
rules ([docs.docker.com](https://docs.docker.com/engine/containers/start-containers-automatically/)):

> A restart policy only takes effect after a container starts successfully. In this case, starting
> successfully means that the container is up for at least 10 seconds and Docker has started
> monitoring it.

> If you manually stop a container, the restart policy is ignored until the Docker daemon restarts
> or the container is manually restarted.

The first rule is a partial crash-loop guard: a container that dies inside 10 s is not restarted at
all under any policy.

### 5.2 Which value suits deliberate exit on unrecoverable configuration error

`on-failure` and `always` and `unless-stopped` all restart a non-zero exit, so a process that exits
non-zero on a bad configuration would loop under any of them until `max-retries` (if set) or the
10 s guard stops it.

Two workable shapes, both supported by the quoted definitions:

- `restart: "no"` — the specification's default. It "does not restart the container under any
  circumstances", so a deliberate exit stays exited. It also means a genuine crash stays down.
- `restart: on-failure:<n>` — bounded retries. The specification allows limiting "the number of
  restart retries the container runtime attempts", which converts an infinite loop into a bounded
  one.

A third shape is available if the process controls its own exit code: exit `0` on an unrecoverable
configuration error and use `restart: on-failure`. The specification restricts `on-failure` to the
case where "the exit code indicates an error", so a zero exit is not restarted while a crash still
is. This puts the loop decision in the application, where the configuration error is diagnosed.

### 5.3 `deploy.restart_policy`

The specification
([deploy.md](https://raw.githubusercontent.com/compose-spec/compose-spec/main/deploy.md)):

> `restart_policy` configures if and how to restart containers when they exit. If `restart_policy`
> is not set, Compose considers the `restart` field set by the service configuration.

That sentence is the precedence rule: `deploy.restart_policy` wins when present, and the service
level `restart` applies only when it is absent. Its fields:

| Field | Documented meaning | Default |
| --- | --- | --- |
| `condition` | `none` — containers are not automatically restarted regardless of the exit status; `on-failure` — the container is restarted if it exits due to an error, which manifests as a non-zero exit code; `any` — containers are restarted regardless of the exit status | `any` |
| `delay` | "How long to wait between restart attempts, specified as a duration." | "The default is 0, meaning restart attempts can occur immediately." |
| `max_attempts` | "How many times to attempt to restart a container before giving up" | "never give up" |
| `window` | "How long to wait before deciding if a restart has succeeded, specified as a duration" | "decide immediately" |

Note the inverted default: service-level `restart` defaults to `no`, while `deploy.restart_policy`
defaults its `condition` to `any`. Declaring an empty-ish `restart_policy` therefore turns restarts
*on*.

`delay` and `max_attempts` together give a documented backoff that the service-level `restart` key
cannot express.

## 6 Signal delivery to the process

### 6.1 PID 1 only

`docker stop` documents the target explicitly
([docs.docker.com](https://docs.docker.com/reference/cli/docker/container/stop/)):

> The main process inside the container will receive `SIGTERM`, and after a grace period, `SIGKILL`.

The signal goes to the main process — PID 1 in the container's namespace. Child processes receive
nothing directly.

### 6.2 What the shell form does to it

The Dockerfile reference is unambiguous
([docs.docker.com](https://docs.docker.com/reference/dockerfile/#entrypoint)):

> The shell form of `ENTRYPOINT` ignores any `CMD` or `docker run` command line arguments.

> It also starts your `ENTRYPOINT` as a subcommand of `/bin/sh -c`, which does not pass signals.

> This means that the executable will not be the container's `PID 1`, and will not receive Unix
> signals.

> In this case, your executable doesn't receive a `SIGTERM` from `docker stop <container>`.

And the remedy:

> To ensure that `docker stop` will signal any long running `ENTRYPOINT` executable correctly, you
> need to remember to start it with `exec`.

There is a related trap when mixing forms:

> If you use the shell form of `CMD` [with exec form ENTRYPOINT], the `ENTRYPOINT` receives a shell
> invocation as its argument rather than the bare command.

The operational rule: use the JSON exec form for `ENTRYPOINT` and for Compose's `command`, or the
25 s drain never begins — the process is SIGKILLed at the grace deadline having never seen SIGTERM.

### 6.3 `init: true`

The specification
([05-services.md](https://raw.githubusercontent.com/compose-spec/compose-spec/main/05-services.md)):

> `init` runs an init process (PID 1) inside the container that forwards signals and reaps
> processes. Set this option to `true` to enable this feature for the service.

> The init binary that is used is platform specific.

So `init: true` inserts a real PID 1 that forwards the stop signal to the application process and
reaps zombies. It fixes signal delivery for a process that is not itself PID 1 and removes the need
for the application to reap children. It does not extend the grace period.

### 6.4 `STOPSIGNAL` in the image

The Dockerfile reference
([docs.docker.com](https://docs.docker.com/reference/dockerfile/#healthcheck), STOPSIGNAL section;
same text upstream in
[moby/buildkit reference.md](https://raw.githubusercontent.com/moby/buildkit/master/frontend/dockerfile/docs/reference.md)):

> The `STOPSIGNAL` instruction sets the system call signal that will be sent to the container to
> exit. This signal can be a signal name in the format `SIG<NAME>`, for instance `SIGKILL`, or an
> unsigned number that matches a position in the kernel's syscall table, for instance `9`. The
> default is `SIGTERM` if not specified.

There is a wording tension worth recording. The Compose specification says "If unset containers are
stopped by Compose by sending `SIGTERM`", which reads as if Compose sends SIGTERM regardless of the
image's `STOPSIGNAL`, while the Dockerfile reference says the image's `STOPSIGNAL` is what gets
sent. The precedence between a Compose `stop_signal` and an image `STOPSIGNAL` is **[unverified]** —
both
sections were read in full and neither states which wins. Set `stop_signal` explicitly in the
Compose file if the signal matters.

## 7 What the evidence supports

The arithmetic is a single subtraction. The drain needs 25 s. Compose's `stop_grace_period` defaults
to 10 s, after which the process is SIGKILLed. Fifteen seconds of drain never happen, on every stop,
recreate and `docker compose down`. Kubernetes' 30 s default leaves 5 s of headroom; Compose's 10 s
default leaves negative 15. **The one thing an operator must change from the default is
`stop_grace_period` — set it above the drain budget, for example `stop_grace_period: 40s`, and never
pass a smaller `-t` to `docker compose down` or `docker compose stop`, because the flag overrides
the file downward.**

Two secondary consequences follow. First, the entrypoint and `command` must use the JSON exec form
(or `init: true` must be set), or the process is not PID 1, never receives SIGTERM, and the drain
does not start at all — in which case the grace period is irrelevant and every stop is a 10 s pause
followed by a kill. Second, Compose gives no liveness equivalent: a `healthcheck` reports a status
and gates `depends_on` at startup, and nothing restarts an unhealthy container. A wedged process
stays wedged until a human notices, so the process must handle its own supervision — or the operator
must accept that health here is an observation, not a control loop.

## Sources

Docker Compose and Docker:

- <https://raw.githubusercontent.com/compose-spec/compose-spec/main/spec.md>
- <https://raw.githubusercontent.com/compose-spec/compose-spec/main/05-services.md>
- <https://raw.githubusercontent.com/compose-spec/compose-spec/main/deploy.md>
- <https://raw.githubusercontent.com/compose-spec/compose-spec/main/schema/compose-spec.json>
- <https://docs.docker.com/reference/compose-file/services/>
- <https://docs.docker.com/reference/compose-file/deploy/>
- <https://docs.docker.com/reference/dockerfile/#entrypoint>
- <https://docs.docker.com/reference/dockerfile/#healthcheck>
- <https://docs.docker.com/reference/cli/docker/container/stop/>
- <https://docs.docker.com/reference/cli/docker/compose/up/>
- <https://docs.docker.com/reference/cli/docker/compose/down/>
- <https://docs.docker.com/reference/cli/docker/compose/stop/>
- <https://docs.docker.com/engine/containers/start-containers-automatically/>
- <https://docs.docker.com/compose/how-tos/startup-order/>
- <https://raw.githubusercontent.com/moby/buildkit/master/frontend/dockerfile/docs/reference.md>
- <https://api.github.com/repos/docker/docs/contents/content/reference>
- <https://docs.docker.com/reference/dockerfile.md>
- <https://docs.docker.com/engine/reference/builder/>
- <https://raw.githubusercontent.com/docker/docs/main/content/reference/dockerfile.md>
- <https://raw.githubusercontent.com/docker/docs/main/content/reference/cli/docker/container/stop.md>
