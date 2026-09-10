# 29. The Kubernetes fields a graceful drain depends on

**Question.** Which Kubernetes fields does a graceful drain depend on, in what order do they fire,
and what does each of them do for a process whose only inbound surface is a probe? The same
questions asked of Docker Compose are
[`docs/research/36`](36-compose-fields-a-drain-depends-on.md).
[ADR-0023](../adr/0023-websocket-gateway-resilience.md) drains "the queue and in-flight handlers
within a grace period (default 25 s inside the 30 s Kubernetes budget)", and
[ADR-0031](../adr/0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md) owes the deployment
view a statement that the process's shutdown budget must exceed that deadline. Every number below
becomes a number in a design document, so every number here is quoted from a primary source.

Gathered for GitHub issue #99. Two notes already cover ground this one does not repeat.
[`docs/research/26`](26-schedule-reliability-and-probe-primitives.md) §7 holds the probe contract,
the probe defaults and the outbound-only case;
[`docs/research/27`](27-application-contributed-readiness-checks.md) §3 holds the termination
sequence in outline, the three EndpointSlice conditions and the list of rollout-pacing fields. This
note answers what they leave open: the exact order and concurrency of the termination steps, the
arithmetic of the grace period, what `preStop` can and cannot be, which probes keep running while a
Pod terminates, which workload kind bounds the replica count, the smallest field set an operator
must set so that a 25 s in-process drain actually completes.

Findings only. Sources are primary — the Kubernetes documentation source under
`kubernetes/website`, the `kubernetes/kubernetes` API and kubelet source, KEP-3960,
`docs.python.org`, the Docker Dockerfile reference, and the source and documentation of each server
and peer project — read on 2026-09-10. The Kubernetes documentation pages cited are the current
ones, which the site header dates **v1.37**. Anything a primary source did not confirm is marked
**[unverified]**.

## 1 The termination sequence, and what runs beside what

The
[Pod lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination)
page states the design aim first: "The design aim is for you to be able to request deletion and
know when processes terminate, but also be able to ensure that deletes eventually complete." The
flow it publishes, condensed to what a single-container Pod does:

1. **A delete request arrives** — from `kubectl`, from a controller replacing the Pod, or from the
   Eviction API. The example the page uses is "You use the `kubectl` tool to manually delete a
   specific Pod, with the default grace period (30 seconds)."
2. **The API server records the deadline first.** "The Pod in the API server is updated with the
   time beyond which the Pod is considered 'dead' along with the grace period." Concretely that is
   `metadata.deletionTimestamp` — "RFC 3339 date and time at which this resource will be deleted …
   set by the server when a graceful deletion is requested by the user, and is not directly
   settable by a client" — together with `metadata.deletionGracePeriodSeconds`, "Number of seconds
   allowed for this object to gracefully terminate before it will be removed from the system. Only
   set when deletionTimestamp is also set. May only be shortened. Read-only." `kubectl describe`
   then shows the Pod as "Terminating".
3. **The kubelet starts local shutdown.** "as soon as the kubelet sees that a Pod has been marked as
   terminating (a graceful shutdown duration has been set), the kubelet begins the local Pod
   shutdown process."
4. **`preStop` runs, before the signal.** "If one of the Pod's containers has defined a `preStop`
   hook and the `terminationGracePeriodSeconds` in the Pod spec is not set to 0, the kubelet runs
   that hook inside of the container." The container-lifecycle-hooks reference is categorical about
   the ordering: "`PreStop` hooks are not executed asynchronously from the signal to stop the
   Container; the hook must complete its execution before the TERM signal can be sent."
5. **The signal goes to PID 1.** "The kubelet triggers the container runtime to send a TERM signal
   to process 1 inside each container." With several containers, "the containers in the Pod receive
   the TERM signal at different times and in an arbitrary order"; the requests "are processed by the
   container runtime asynchronously" and "There is no guarantee to the order of processing for these
   requests."
6. **Endpoint re-evaluation runs beside steps 3–5, and removal is not immediate.** "At the same time
   as the kubelet is starting graceful shutdown of the Pod, the control plane evaluates whether to
   remove that shutting-down Pod from EndpointSlice objects, where those objects represent a Service
   with a configured selector." What is concurrent is the *evaluation*: "Any endpoints that
   represent the terminating Pods are not immediately removed from EndpointSlices, and a status
   indicating terminating state is exposed from the EndpointSlice API." The same step does remove
   the Pod from the workload controller's view: "ReplicaSets and other workload resources no longer
   treat the shutting-down Pod as a valid, in-service replica."
7. **SIGKILL on expiry.** "When the grace period expires, if there is still any container running in
   the Pod, the kubelet triggers forcible shutdown. The container runtime sends `SIGKILL` to any
   processes still running in any container in the Pod." The kubelet then moves the Pod to a
   terminal phase, "triggers forcible removal of the Pod object from the API server, by setting
   grace period to 0", and "The API server deletes the Pod's API object, which is then no longer
   visible from any client."

Three things about this list matter to a design.

- **Step 6 is concurrent with steps 3–5, and the parallelism is the whole race.** Nothing in the
  sequence makes endpoint re-evaluation precede SIGTERM. That is why a `preStop` sleep exists at all
  (§3).
- **The signal is not necessarily TERM.** "Many container runtimes respect the `STOPSIGNAL` value
  defined in the container image and, if different, send the container image configured STOPSIGNAL
  instead of TERM", and "If no stop signal is defined in the image, the default signal of the
  container runtime (SIGTERM for both containerd and CRI-O) would be used to kill the container."
  `lifecycle.stopSignal` can override the image, but only behind a gate that is off: "If the
  `ContainerStopSignals` feature gate is enabled, you can configure a custom stop signal for your
  containers from the container Lifecycle", with a second precondition, "We require the Pod's
  `spec.os.name` field to be present as a requirement for defining stop signals in the container
  lifecycle." The gate descriptor records a single stage — alpha, `defaultValue: false`,
  `fromVersion: "1.33"` — so on a stock cluster the field is unavailable and the image's
  `STOPSIGNAL` is the only lever. The generated API text says the same: "StopSignal defines which
  signal will be sent to a container when it is being stopped. If not specified, the default is
  defined by the container runtime in use. StopSignal can only be set for Pods with a non-empty
  .spec.os.name".
- **A kubelet restart restarts the clock.** "If the kubelet or the container runtime's management
  service is restarted while waiting for processes to terminate, the cluster retries from the start
  including the full original grace period." A drain must therefore be idempotent, not
  single-shot.

Sidecars change the order and are worth naming even though the target process has none: the kubelet
"will delay sending the TERM signal to these sidecar containers until the last main container has
fully terminated", terminating them "in the reverse order they are defined in the Pod spec", and
"slow termination of a main container will also delay the termination of the sidecar containers."

## 2 The grace-period arithmetic

`terminationGracePeriodSeconds` is a PodSpec field. Its API description is the authority on all of
it: "Optional duration in seconds the pod needs to terminate gracefully. May be decreased in delete
request. Value must be non-negative integer. The value zero indicates stop immediately via the kill
signal (no opportunity to shut down). If this value is nil, the default grace period will be used
instead. The grace period is the duration in seconds after the processes running in the pod are sent
a termination signal and the time when the processes are forcibly halted with a kill signal. Set
this value longer than the expected cleanup time for your process. Defaults to 30 seconds."

**The clock starts before `preStop`, not at SIGTERM.** The API text above defines the period as
running from the termination signal, but the hook reference contradicts that reading and is the
operative one: "The Pod's termination grace period countdown begins before the `PreStop` hook is
executed, so regardless of the outcome of the handler, the container will eventually terminate
within the Pod's termination grace period." The generated API description of `lifecycle.preStop`
says the same and adds the exception: "the container will eventually terminate within the Pod's
termination grace period (unless delayed by finalizers)."

**`preStop` and SIGTERM share one budget, and the documentation does the sum for you.** "This grace
period applies to the total time it takes for both the `PreStop` hook to execute and for the
Container to stop normally. If, for example, `terminationGracePeriodSeconds` is 60, and the hook
takes 55 seconds to complete, and the Container takes 10 seconds to stop normally after receiving
the signal, then the Container will be killed before it can stop normally, since
`terminationGracePeriodSeconds` is less than the total time (55+10) it takes for these two things to
happen."

**The documented "2 seconds" is a floor on the container's stop window, not an extension handed to
the hook.** The documentation's wording is loose: "If the `preStop` hook is still running after the
grace period expires, the kubelet requests a small, one-off grace period extension of 2 seconds."
The kubelet source shows what that is. `killContainer` computes the budget, subtracts what the hook
consumed — `gracePeriod = gracePeriod - m.executePreStopHook(ctx, pod, containerID, containerSpec,
gracePeriod)` — then raises an exhausted budget back up under the comment "always give containers a
minimal shutdown window to avoid unnecessary SIGKILLs": `if gracePeriod <
minimumGracePeriodInSeconds { gracePeriod = minimumGracePeriodInSeconds }`, and passes the floored
value to `m.runtimeService.StopContainer(ctx, containerID.ID, gracePeriod)`. The constant is
declared as `minimumGracePeriodInSeconds = 2` with the comment "A minimal shutdown window for
avoiding unnecessary SIGKILLs". The hook itself receives no extension: `executePreStopHook` selects
on `case <-time.After(time.Duration(gracePeriod) * time.Second):` and abandons the hook when that
elapses, logging "PreStop hook not completed in grace period". So the application is floored at 2 s
of stop window after the signal — two seconds, not twenty-five.

The accompanying note tells the operator that the floor is not a budget: "If the `preStop` hook
needs longer to complete than the default grace period allows, you must modify
`terminationGracePeriodSeconds` to suit this." A hook that hangs does not buy the application
anything either: "If a `PreStop` hook hangs during execution, the Pod's phase will be `Terminating`
and remain there until the Pod is killed after its `terminationGracePeriodSeconds` expires." The
Pod-lifecycle page names the outcome of an overrun: "Similarly, if the Pod has a `preStop` hook that
exceeds the termination grace period, emergency termination may occur." The same section describes
that path, for the grace period expiring before termination completes, as "all remaining containers
in the Pod will be terminated simultaneously with a short grace period."

**Overrides at delete time.** `kubectl delete --grace-period` is an `int` documented with "Default:
-1" and the text "Period of time in seconds given to the resource to terminate gracefully. Ignored
if negative. Set to 1 for immediate shutdown. Can only be set to 0 when --force is true (force
deletion)." The default being negative is what makes a plain `kubectl delete` inherit the Pod's own
value rather than impose one; the synopsis says so: "These resources define a default period before
they are forcibly terminated (the grace period) but you may override that value with the
--grace-period flag, or pass --now to set a grace-period of 1." The API only allows shortening —
`deletionTimestamp` "may not be unset or be set further into the future, although it may be
shortened". Forced deletion
is the extreme: "Setting the grace period to `0` forcibly and immediately deletes the Pod from the
API server", with "--force" required alongside, and "When a force deletion is performed, the API
server does not wait for confirmation from the kubelet that the Pod has been terminated on the node
it was running on."

**There is no `--pod-max-grace-period`.** The flag does not exist. The kubelet command-line
reference contains no entry with that name, and `cmd/kubelet/app/options/options.go` registers only
two flags whose names contain `grace` — `eviction-soft-grace-period` and
`eviction-max-pod-grace-period`, the latter documented as "Maximum allowed grace period (in seconds)
to use when terminating pods in response to a soft eviction threshold being met. If negative, defer
to pod specified value." (Established by asking for the exact substring `pod-max-grace-period` in
both files and getting no match.)

**The node can truncate the budget from underneath.** Graceful node shutdown is a separate clock:
`shutdownGracePeriod` "Specifies the total duration that the node should delay the shutdown by" and
`shutdownGracePeriodCriticalPods` "Specifies the duration used to terminate critical pods during a
node shutdown", and "by default, both configuration options described below, `shutdownGracePeriod`
and `shutdownGracePeriodCriticalPods`, are set to zero", so the feature does nothing until a cluster
administrator configures it. When it is configured, an ordering by `PriorityClass` applies through
`shutdownGracePeriodByPodPriority`.

The page publishes one worked example, and it is the only arithmetic Kubernetes documents for a
node-level clock subdividing a Pod's window: "For example, if `shutdownGracePeriod=30s`, and
`shutdownGracePeriodCriticalPods=10s`, kubelet will delay the node shutdown by 30 seconds. During
the shutdown, the first 20 (30-10) seconds would be reserved for gracefully terminating normal pods,
and the last 10 seconds would be reserved for terminating critical pods." A non-critical Pod on a
node configured that way therefore has 20 s, not the 30 s its own spec asks for. Whether a Pod grace
period longer than the node's share is truncated or merely overrun is still **[unverified — the
node-shutdown page was read in full and contains no sentence stating what happens when
`terminationGracePeriodSeconds` exceeds the node's shutdown grace period; the arithmetic above is
the closest the page comes]**.

## 3 `preStop`: the three handlers, the `sleep` action, and what it is documented for

The
[container lifecycle hooks](https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/)
page lists exactly three handler kinds: "Exec - Executes a specific command, such as `pre-stop.sh`,
inside the cgroups and namespaces of the Container. Resources consumed by the command are counted
against the Container.", "HTTP - Executes an HTTP request against a specific endpoint on the
Container.", and "Sleep - Pauses the container for a specified duration." A fourth, `tcpSocket`, is
still accepted by the API and is marked deprecated in the reference; the page also records **where**
each runs: "`httpGet`, `tcpSocket` (deprecated) and `sleep` are executed by the kubelet process, and
`exec` is executed in the container."

**`lifecycle.preStop.sleep` is now stable and needs nothing enabled.** The feature-gate descriptors
in the documentation source record the graduation. `PodLifecycleSleepAction` — "Enables the `sleep`
action in Container lifecycle hooks (`preStop` and `postStart`)" — was alpha in **1.29** (default
`false`), beta from **1.30** to **1.33** (default `true`) and is **stable and locked from 1.34**. A
zero duration needed a second gate: `PodLifecycleSleepActionAllowZero` was alpha in **1.32**, beta
in **1.33**, and is **stable and locked from 1.34**. The API surface is one field: `SleepAction`
"describes a \"sleep\" action", carrying `seconds`, "Seconds is the number of seconds to sleep."

**The bounds are enforced at admission, and the upper bound is the grace period.** KEP-3960 states
both, as validation requirements: "Test that the validation returns an error when given an invalid
duration value (e.g., a negative value)." and "Test that the validation returns an error when given
duration is longer than the termination graceperiod." It also fixes the zero case at the handler:
"Test that the `runSleepHandler` function returns immediately when given a duration of zero." So on
a current cluster zero is accepted and returns at once, a negative value is rejected, and a sleep
longer than `terminationGracePeriodSeconds` is rejected at admission rather than discovered at drain
time. The exact comparison operator and rejection message in `validateSleepAction`
(`pkg/apis/core/validation/validation.go`) are **[unverified — the file was fetched twice from
`raw.githubusercontent.com` and truncated before that function both times, so neither the operator
nor the message string was read; whether the boundary case `sleep.Seconds ==
terminationGracePeriodSeconds` is accepted is therefore open]**.

**Every documented purpose of a `preStop` sleep is about endpoint propagation.** KEP-3960, which
added the action, gives the use case as "Allowing a smooth transition in load balancers or service
meshes" so that "the Endpoint Controller will remove the terminating pod, and the traffic will be
sent to other running pods", and gives the reason for making it native as convenience: the previous
recipe "requires me to have a sleep binary in my image, and I want to do this more conveniently".
Its non-goal is explicit — "This KEP does not aim to provide a way to pause or delay pod termination
indefinitely."

`preStop` in general, however, is documented for two purposes that have nothing to do with a
Service. The hooks page says "There are cases, however, when long running commands make sense, such
as when saving state prior to stopping a Container", and the Pod-lifecycle page offers it as an
ordering primitive: "If the order of shutdowns matters, consider using a `preStop` hook to
synchronize (or switch to using sidecar containers)." The accurate claim is therefore narrow:
**every documented purpose of a `preStop` *sleep* is endpoint propagation, while `preStop` itself
is also documented for state-saving and for shutdown ordering** **[the sleep half established by a
code
search over `content/en/docs` in `kubernetes/website` for pages containing both `preStop` and
`sleep`, which returns four files and no fifth purpose: the two hook and lifecycle concept pages,
the `PodLifecycleSleepAction` feature-gate stub, and the generated `pod-v1` API reference]**.
Neither of the two non-Service purposes applies here: this design saves no state from a hook and has
one container to order, and the drain runs in-process rather than in a hook.

Two more hook facts push the same way. A hook is not a reliable one-shot: "Hook delivery is intended
to be *at least once*, which means that a hook may be called multiple times for any given event,
such as for `PostStart` or `PreStop`. It is up to the hook implementation to handle this correctly",
because "if a kubelet restarts in the middle of sending a hook, the hook might be resent after the
kubelet comes back up." And a hook is itself a kill path: "If either a `PostStart` or `PreStop` hook
fails, it kills the Container." For a process whose only inbound surface is a probe, a `preStop`
sleep buys nothing: there is no EndpointSlice to propagate out of, the sleep is subtracted from the
same budget the drain needs, and any non-sleep hook adds a way for the container to die early.

## 4 What reaches the process, and what a Python process must do to receive it

**The signal goes to PID 1 of the container and nowhere else.** "The kubelet triggers the container
runtime to send a TERM signal to process 1 inside each container." Nothing in the Pod-lifecycle page
promises delivery to any other process in the container.

**A shell entry point eats it.** The Dockerfile reference states the consequence of the shell form
directly: it "starts your `ENTRYPOINT` as a subcommand of `/bin/sh -c`, which does not pass
signals", and "In this case, your executable doesn't receive a `SIGTERM` from `docker stop
<container>`." The exec form — a JSON array — is the form that makes the application PID 1. This is
not hypothetical for this domain: FastStream's own published Kubernetes Deployment runs
`command: ["/bin/sh", "-c", 'python3 main.py']` (§11).

**A process that ignores the signal is killed, not waited for.** "Once the grace period has expired,
the KILL signal is sent to any remaining processes, and the Pod is then deleted from the API
Server." There is no escalation ladder and no second TERM.

On the Python side, three facts bound what a handler can be.

- **`loop.add_signal_handler` is the only handler that may touch the loop.** "The callback will be
  invoked by *loop*, along with other queued callbacks and runnable coroutines of that event loop.
  Unlike signal handlers registered using `signal.signal`, a callback registered with this function
  is allowed to interact with the event loop." It raises `ValueError` for an invalid or uncatchable
  signal, `RuntimeError` if the handler cannot be set up, "must be invoked in the main thread", and
  is available on Unix only. The `asyncio` documentation's own example registers exactly `SIGINT`
  and `SIGTERM` this way and calls `loop.stop()`.
- **`signal.signal` runs between bytecodes, in the main thread, and cannot safely call loop
  methods.** "A Python signal handler does not get executed inside the low-level (C) signal handler.
  Instead, the low-level signal handler sets a flag which tells the virtual machine to execute the
  corresponding Python signal handler at a later point (for example, at the next bytecode
  instruction)." Two consequences bite a drain: "A long-running calculation implemented purely in C
  … may run uninterrupted for an arbitrary amount of time, regardless of any signals received. The
  Python signal handlers will be called when the calculation finishes", and "If the handler raises
  an exception, it will be raised 'out of thin air' in the main thread." Handlers "are always
  executed in the main Python thread of the main interpreter", and "only the main thread of the main
  interpreter is allowed to set a new signal handler."
- **`asyncio.Runner` owns SIGINT and nothing else.** The documented mechanism is four steps:
  "`asyncio.Runner.run` installs a custom `signal.SIGINT` handler before any user code is executed
  and removes it when exiting from the function"; the Runner "creates the main task for the passed
  coroutine"; on SIGINT "the custom signal handler cancels the main task by calling
  `asyncio.Task.cancel` which raises `asyncio.CancelledError` inside the main task. This causes the
  Python stack to unwind, `try/except` and `try/finally` blocks can be used for resource cleanup.
  After the main task is cancelled, `asyncio.Runner.run` raises `KeyboardInterrupt`"; and the escape
  hatch is "A user could write a tight loop which cannot be interrupted by `asyncio.Task.cancel`, in
  which case the second following Ctrl-C immediately raises the `KeyboardInterrupt` without
  cancelling the main task." **SIGTERM gets none of this.** Nothing in `asyncio.run` or
  `asyncio.Runner` installs a SIGTERM handler, so an asyncio program under Kubernetes dies on the
  default disposition unless it registers one itself, and a *second* SIGTERM has no documented
  effect at all — the second-signal escape hatch exists only for SIGINT.

**A SIGINT arriving mid-drain lets the drain's cleanup finish; a second one does not.** The order in
step 3 above is explicit and it is the answer for a drain already in progress: the `CancelledError`
is raised inside the main task, "This causes the Python stack to unwind, `try/except` and
`try/finally` blocks can be used for resource cleanup. After the main task is cancelled,
`asyncio.Runner.run` raises `KeyboardInterrupt`" — the `KeyboardInterrupt` comes *after* the
cancellation has unwound, so a `finally` block around the drain runs to completion first. The
cancellation reaches the drain only at its next suspension point: `Task.cancel` "arranges for a
`CancelledError` exception to be thrown into the wrapped coroutine on the next cycle of the event
loop", and "If the Task being cancelled is currently awaiting on a future-like object, that awaited
object will also be cancelled. This cancellation propagates down the entire chain of awaited
objects." Step 4 is the case that loses the cleanup: on the second Ctrl-C the `KeyboardInterrupt` is
raised "immediately … without cancelling the main task", so it lands out of thin air wherever the
drain happens to be, and its own `finally` blocks are what have to survive it. Under Kubernetes this
path is a `kubectl` foreground interrupt, not the platform: the kubelet sends one stop signal and
then SIGKILL.

One further number belongs to the process budget rather than to Kubernetes: `asyncio.run` states
"The executor is given a timeout duration of 5 minutes to shutdown. If the executor hasn't finished
within that duration, a warning is emitted and the executor is closed." A blocking call parked in
the default executor can therefore hold the runner well past any Pod grace period — which is exactly
the abandoned-thread case ADR-0023 reports through `HandlerAbandoned`.

## 5 Probes during termination

The documentation answers the readiness half in one sentence — "Readiness probes run on the
container during its whole lifecycle." — and leaves the liveness and startup half to the kubelet
source, which answers it twice over.

`Kubelet.SyncTerminatingPod` calls `kl.probeManager.StopLivenessAndStartup(pod)` **before**
`kl.killPod(...)`, and calls `kl.probeManager.RemovePod(pod)` only after `killPod` returns, under
the comment "Once the containers are stopped, we can stop probing for liveness and readiness."
`prober.Manager.StopLivenessAndStartup` is declared as "StopLivenessAndStartup handles stopping
liveness and startup probes during termination" and its body walks the Pod's containers stopping
only the workers whose `probeType` is `liveness` or `startup`. `RemovePod` is the one that
"handles cleaning up the removed pod state, including terminating probe workers and deleting cached
results."

The probe worker does not wait to be told. `doProbe` in `pkg/kubelet/prober/worker.go`
short-circuits on the API object alone: `if w.pod.ObjectMeta.DeletionTimestamp != nil &&
(w.probeType == liveness || w.probeType == startup)` logs "Pod deletion requested, setting probe
result to success", calls `w.resultsManager.Set(w.containerID, results.Success, w.pod)` and returns
false. That fires as soon
as `deletionTimestamp` is set — before the kubelet's local shutdown begins — and the last recorded
liveness result for a terminating Pod is therefore forced to Success, not merely left stale. The
same function bounds how long the readiness worker survives: it returns false at the guard "Worker
should terminate if pod is terminated." on `status.Phase == v1.PodFailed || status.Phase ==
v1.PodSucceeded`, and when `c.State.Running == nil` it records `results.Failure` before deciding
whether to keep going. Readiness gets neither the deletion short-circuit nor the forced Success.

So, for the whole drain window:

- **Liveness and startup probes stop at the very start of termination, twice over.** The worker
  forces Success the moment `deletionTimestamp` is set, and the manager stops the workers when local
  shutdown begins. A liveness failure cannot restart or kill a container that is already draining.
  The drain does not need liveness to be lenient; it needs nothing from liveness at all.
- **The readiness probe keeps being asked until the containers are actually stopped** — and at the
  defaults that is a handful of questions, not one. `periodSeconds` is "How often (in seconds) to
  perform the probe. Default to 10 seconds. The minimum value is 1." and `failureThreshold` is
  "Defaults to 3. Minimum value is 1.", so a 25 s drain sees roughly two or three readiness answers
  and never reaches three consecutive failures from a standing start.
- **For this workload, nothing consumes those answers.** The Spring-style "readiness flips on
  shutdown, liveness does not" rule
  ([`docs/research/27`](27-application-contributed-readiness-checks.md) §3) is implementable here,
  but it is a no-op once the delete request lands. The EndpointSlice consumer needs "a Service with
  a configured selector", which this Pod has none of. The replica accounting drops the Pod:
  `IsPodActive` is `v1.PodSucceeded != p.Status.Phase && v1.PodFailed !=
  p.Status.Phase && p.DeletionTimestamp == nil`, and `FilterActivePods` — "returns pods that have
  not terminated" — keeps only those, so `minReadySeconds` and `maxUnavailable` stop counting a Pod
  with a `deletionTimestamp`. The PDB drops out too, by `canIgnorePDB` (§7). The `Ready` condition
  therefore matters *before* the delete request and not during the drain — which is also what the
  probes page says: "If you want to be able to drain requests when the Pod is deleted, you do not
  necessarily need a readiness probe; when the Pod is deleted, the corresponding endpoint in the
  EndpointSlice will update its conditions: the endpoint ready condition will be set to false, so
  load balancers will not use the Pod for regular traffic."
- **The endpoint answer is decided without the probe anyway.** "Terminating endpoints always have
  their `ready` status as `false` (for backward compatibility with versions before 1.26), so load
  balancers will not use it for regular traffic", and "If traffic draining on terminating Pod is
  needed, the actual readiness can be checked as a condition `serving`."

What the probe endpoint should answer during the drain follows: **failing is honest and harmless,
succeeding is equally harmless, and the probe's real job is over before the drain starts.** Keep a
readiness probe for what it does pace — the rollout, through `minReadySeconds` and the PDB, while
the Pod is not yet terminating — and do not build any drain behaviour on top of it.

**Probe-level `terminationGracePeriodSeconds` overrides the Pod value for a probe-initiated kill,
and only for liveness and startup.** The field description: "Optional duration in seconds the pod
needs to terminate gracefully upon probe failure. … If this value is nil, the pod's
terminationGracePeriodSeconds will be used. Otherwise, this value overrides the value provided by
the pod spec. Value must be non-negative integer. The value zero indicates stop immediately via the
kill signal (no opportunity to shut down). … Minimum value is 1." The probes page adds the two rules
an operator needs: "When both a pod- and probe-level `terminationGracePeriodSeconds` are set, the
kubelet will use the probe-level value", and "Probe-level `terminationGracePeriodSeconds` **cannot**
be set for readiness probes. It will be rejected by the API server." The kubelet's own precedence
order shows why this is not a way to give a normal delete a different budget:
`setTerminationGracePeriod` tests `case pod.DeletionGracePeriodSeconds != nil: return
*pod.DeletionGracePeriodSeconds` first, and reaches the probe override only under
`reasonStartupProbe` and `reasonLivenessProbe`. A delete always carries
`DeletionGracePeriodSeconds`, so the probe field is never consulted on that path.

## 6 The workload kind for a process that must never have two live instances

`.spec.strategy` "specifies the strategy used to replace old Pods by new ones", and
`.spec.strategy.type` "can be \"Recreate\" or \"RollingUpdate\". \"RollingUpdate\" is the default
value."

Under the default, two fields set the window in which old and new Pods coexist. Both live under
`.spec.strategy.rollingUpdate`, and the API reference marks the whole block as conditional: the
`rollingUpdate` field is "Rolling update config params. Present only if DeploymentStrategyType =
RollingUpdate." Choosing `Recreate` therefore does not merely make `maxSurge` and `maxUnavailable`
ineffective — it removes the block they live in. `.spec.strategy.rollingUpdate.maxUnavailable` and
`.spec.strategy.rollingUpdate.maxSurge` both take "an absolute number (for example, 5) or a
percentage of desired Pods (for example, 10%)", and for each "The default value is 25%." The page's
own worked example shows what surge means: with 30%, "the total number of Pods running at any time
during the update is at most 130% of desired Pods." The rounding rules decide the single-replica
case, and they point opposite ways: for `maxUnavailable` "The absolute number is calculated from
percentage by rounding down", for `maxSurge` "The absolute number is calculated from the percentage
by rounding up". At one replica
the defaults therefore give `maxUnavailable` 0 and `maxSurge` 1 — a second Pod is created before the
first is gone, and the new process is live while the old one still holds its outbound connection.
The pair also cannot both be zeroed: "The value cannot be 0 if
`.spec.strategy.rollingUpdate.maxSurge` is 0."

`Recreate` inverts that: "All existing Pods are killed before new ones are created when
`.spec.strategy.type==Recreate`." Its note is the closest Kubernetes comes to an explicit statement
that a Deployment cannot bound the replica count, and it is worth quoting whole. "This will only
guarantee Pod termination previous to creation for upgrades." "If you upgrade a Deployment, all Pods
of the old revision will be terminated immediately." "Successful removal is awaited before any Pod
of the new revision is created." "If you manually delete a Pod, the lifecycle is controlled by the
ReplicaSet and the replacement will be created immediately (even if the old Pod is still in a
Terminating state)." "If you need an \"at most\" guarantee for your Pods, you should consider using
a StatefulSet." So `Recreate` bounds an *upgrade* and nothing else: node drain, eviction, preemption
and a manual delete all still produce an overlap.

A StatefulSet is where the guarantee is named. The task page on force deletion states it as a
property of the controller — "StatefulSet ensures that, at any time, there is at most one Pod with a
given identity running in a cluster", "This is referred to as *at most one* semantics provided by a
StatefulSet" — and states what breaks it: force deletion "can lead to the duplication of a
still-running Pod, and if said Pod can still communicate with the other members of the StatefulSet,
will violate the at most one semantics that StatefulSet is designed to guarantee." The mechanics
behind it are the ordering guarantees: "Ordered, graceful deployment and scaling. Ordered, automated
rolling updates."; "When Pods are being deleted, they are terminated in reverse order, from
{N-1..0}."; "Before a Pod is terminated, all of its successors must be completely shutdown."; and on
update, the controller deletes and recreates "each Pod one at a time", where "The Kubernetes control
plane waits until an updated Pod is Running and Ready prior to updating its predecessor." The
default `podManagementPolicy` is the one that provides this: "`OrderedReady` pod management is the
default for StatefulSets", against `Parallel`, which "tells the StatefulSet controller to launch or
terminate all Pods in parallel".

| Choice | What it bounds | What it costs |
|---|---|---|
| Deployment, `RollingUpdate` (default) | nothing — `maxSurge` 25% admits an overlapping Pod | two live consumers during every rollout |
| Deployment, `Recreate` | upgrades only: old Pods removed before new ones are created | a full outage window per rollout; no guarantee on delete, eviction or preemption |
| StatefulSet, `OrderedReady`, `RollingUpdate` | "at most one Pod with a given identity" at any time | ordered, one-at-a-time rollouts; force deletion voids the guarantee |

The honest reading is that no workload kind removes the need for an application-level lease. The
StatefulSet guarantee is stated for a Pod *identity*, and it is voided by force deletion and by the
network partitions the `deletionTimestamp` text warns about — "In the presence of network
partitions, this object may still exist after this timestamp". ADR-0023's single-consumer lease over
a distributed `LockProvider` is the mechanism that holds when the platform's does not.

## 7 The fields that pace a rollout through the Pod `Ready` condition

[`docs/research/27`](27-application-contributed-readiness-checks.md) §3 lists these; each default
below is re-read against its own page.

- **`minReadySeconds`** — "the minimum number of seconds for which a newly created Pod should be
  ready without any of its containers crashing, for it to be considered available. This defaults to
  0". The StatefulSet page carries its own copy of the field with the same default and spells out
  what the default means: "This field defaults to 0 (the Pod will be considered available as soon as
  it is ready)."
- **`progressDeadlineSeconds`** — "the number of seconds you want to wait for your Deployment to
  progress before the system reports back that the Deployment has failed progressing… This defaults
  to 600."
- **`maxUnavailable` / `maxSurge`** — "The default value is 25%." for each, as in §6.
- **PodDisruptionBudget** — "A PDB limits the number of Pods of a replicated application that are
  down simultaneously from voluntary disruptions." `.spec.minAvailable` is the "number of pods from
  that set that must still be available after the eviction" and `.spec.maxUnavailable` the "number
  of pods from that set that can be unavailable after the eviction"; either "can be either an
  absolute number or a percentage", and neither carries a default.

Three PDB facts decide what it does for a draining Pod.

- **Healthy means the `Ready` condition, and nothing else.** "The current implementation considers
  healthy pods, as pods that have `.status.conditions` item with `type=\"Ready\"` and
  `status=\"True\"`." The registry code says the same in one line: "IsPodReady is the current
  implementation of IsHealthy".
- **A PDB stops an eviction from starting; it does not protect a Pod that is already draining.**
  `pkg/registry/core/pod/storage/eviction.go` short-circuits the budget check entirely for such a
  Pod: `canIgnorePDB` "returns true for pod conditions that allow the pod to be deleted without
  checking PDBs" when the phase is `Succeeded`, `Failed` or `Pending`, **or**
  `!pod.ObjectMeta.DeletionTimestamp.IsZero()` — with the comment "Evicting a terminal pod should
  result in direct deletion of pod as it already caused disruption by the time we are evicting.
  There is no need to check for pdb." Once `deletionTimestamp` is set, the budget is out of the
  picture and only `terminationGracePeriodSeconds` protects the drain.
- **`unhealthyPodEvictionPolicy` decides the not-yet-ready case, and its default is the strict
  one.** "The default behavior when no policy is specified corresponds to the `IfHealthyBudget`
  policy": running but not yet healthy pods "can be evicted only if the guarded application is not
  disrupted", while under `AlwaysAllow` they "are considered disrupted and can be evicted regardless
  of whether the criteria in a PDB is met".

Two boundary conditions complete the picture, and at one replica they are the same condition.
Setting a budget that admits nothing is legal and documented: "If you set `maxUnavailable` to 0% or
0, or you set `minAvailable` to 100% or the number of replicas, you are requiring zero voluntary
evictions." At `replicas: 1`, `minAvailable: 1` **is** that setting. The consequence is not that the
drain waits: "When you set zero voluntary evictions for a workload object such as ReplicaSet, then
you cannot successfully drain a Node running one of those Pods. If you try to drain a Node where an
unevictable Pod is running, the drain never completes. This is permitted as per the semantics of
`PodDisruptionBudget`." The page's own advice for this shape of workload is a process, not a field:
under "Do not terminate this application without talking to me" it offers "Possible Solution 1: Do
not use a PDB and tolerate occasional downtime." and "Possible Solution 2: Set PDB with
`maxUnavailable=0`. Have an understanding (outside of Kubernetes) that the cluster operator needs to
consult you before termination. When the cluster operator contacts you, prepare for downtime, and
then delete the PDB to indicate readiness for disruption. Recreate afterwards." A PDB also
constrains only the eviction path — "Not all voluntary disruptions are
constrained by Pod Disruption Budgets. For example, deleting deployments or pods bypasses Pod
Disruption Budgets" — and does not prevent involuntary loss: "Involuntary disruptions cannot be
prevented by PDBs; however they do count against the budget."

## 8 Every field a drain touches, its default, and what the default costs

| Field | Where | Default | What breaks at the default |
|---|---|---|---|
| `terminationGracePeriodSeconds` | PodSpec | `30` | 30 s is the whole budget for `preStop` **plus** the process; a 25 s drain fits with 5 s to spare and nothing else in the budget. Unstated, it is a number nobody owns. |
| `terminationGracePeriodSeconds: 0` | PodSpec | — | `preStop` is skipped entirely and the API text is "stop immediately via the kill signal (no opportunity to shut down)". No drain at all. |
| `terminationGracePeriodSeconds` | Probe | inherits the Pod value | only applies to a probe-initiated kill; rejected on a readiness probe; minimum 1. Nothing breaks by omitting it. |
| `lifecycle.preStop` | Container | absent | absent is correct here: every documented purpose of a `preStop` *sleep* is endpoint propagation (§3), the two non-sleep purposes are state-saving and shutdown ordering, which this design needs from neither, and any hook is charged against the same budget the drain needs. |
| `lifecycle.preStop.sleep.seconds` | Container | — | admission rejects `< 0` and anything `> terminationGracePeriodSeconds`; `0` is legal from 1.34. |
| `lifecycle.stopSignal` | Container | unsettable — `ContainerStopSignals` is alpha, `defaultValue: false` from 1.33, and the field also needs `spec.os.name` | on a stock cluster the image's `STOPSIGNAL` is the only lever, and it silently changes which signal arrives; a handler registered only for SIGTERM then never runs. |
| entry point form | image / `command` | image-dependent | shell form "starts your `ENTRYPOINT` as a subcommand of `/bin/sh -c`, which does not pass signals" — PID 1 is the shell, the process never sees the signal, and the entire budget elapses before SIGKILL. |
| SIGTERM handler | the process | none in `asyncio` | `asyncio.Runner` installs a handler for SIGINT only; with none for SIGTERM the default disposition ends the process on the first signal and the drain never starts. |
| `strategy.type` | Deployment | `RollingUpdate` | with `maxSurge` 25%, a new Pod is created before the old one is gone — two live consumers per rollout. |
| `strategy.rollingUpdate.maxSurge` | Deployment | `25%` | see above. `0` is the only value that forbids the overlap, and then `maxUnavailable` must be non-zero. Inapplicable under `Recreate`: the `rollingUpdate` block is "Present only if DeploymentStrategyType = RollingUpdate." |
| `strategy.rollingUpdate.maxUnavailable` | Deployment | `25%` | at one replica the rollout cannot proceed with both at 0; the pair has to be chosen together. Same `Recreate` caveat. |
| `minReadySeconds` | Deployment, StatefulSet | `0` | a new Pod counts as available the instant it reports Ready, so a revision that connects and then fails is never caught by the rollout. |
| `progressDeadlineSeconds` | Deployment | `600` | a stuck rollout is reported after 10 minutes; nothing about a drain breaks. |
| `podManagementPolicy` | StatefulSet | `OrderedReady` | the default is the one that gives the ordering; `Parallel` gives it up. |
| PodDisruptionBudget | namespace object | none | with no PDB a node drain evicts the only replica immediately; with one, the budget still stops guarding the moment `deletionTimestamp` is set. |
| `unhealthyPodEvictionPolicy` | PDB | `IfHealthyBudget` | a Pod that is running but not Ready is guarded by the budget, so a stuck instance can block a node drain until it is forced. |
| liveness probe | Container | absent | irrelevant to a drain: the worker forces `results.Success` once `deletionTimestamp` is set, and `StopLivenessAndStartup` stops the workers at the first step of termination (§5). |
| readiness probe | Container | absent = Success | the `Ready` condition it drives paces the rollout *before* the delete; once `deletionTimestamp` is set, `FilterActivePods`, `canIgnorePDB` and the Service-selector requirement all exclude the Pod, so the answers given during the drain have no consumer. |
| `periodSeconds` | Probe | `10` s, "The minimum value is 1." | a 25 s drain is asked for readiness two or three times; at the default nothing about the drain depends on the answer. |
| `failureThreshold` | Probe | `3` | three consecutive failures are unreachable inside a 25 s drain at the default period; a probe that flips on shutdown never crosses the threshold before the Pod is gone. |
| `--grace-period` | `kubectl delete` | `-1` | negative means "Ignored", so a plain delete inherits the Pod's value; an explicit `--grace-period 5` shortens the budget under a drain that needs 25 s. |
| `shutdownGracePeriod` | KubeletConfiguration | `0` (feature does nothing) | a node shutdown gives Pods no ordered window at all; once configured, a normal Pod gets `shutdownGracePeriod` minus `shutdownGracePeriodCriticalPods` — 20 s of a 30 s setting — not what its own spec asks for. Not something a workload manifest can set. |

## 9 The smallest field set for a 25 s drain, and what a shorter budget does

ADR-0023 drains "within a grace period (default 25 s inside the 30 s Kubernetes budget)". Turning
that into a manifest needs **four** things set and one deliberately left out. Two of the four are
Kubernetes fields — `terminationGracePeriodSeconds`, and the workload kind together with its
`.spec.strategy.type` — and two are not Kubernetes at all: the container image's entry-point form
and the process's own signal handler. That split is the finding: half of a correct drain is outside
the manifest, and no amount of Kubernetes configuration reaches it.

1. **`spec.template.spec.terminationGracePeriodSeconds: 30`, written down rather than inherited.**
   The value equals the default, so the manifest changes nothing — but the field is the contract
   between ADR-0023's 25 s deadline and the platform. The invariant is
   `terminationGracePeriodSeconds` ≥ drain deadline + everything outside the drain's own clock, and
   here that leaves 5 s. The margin has to cover signal delivery, the close handshake, plugin stop
   in reverse topological order, and the ASGI host's lifespan shutdown if one is hosted — which
   uvicorn and granian do not bound at all (§10). Set it explicitly, and raise it whenever the drain
   deadline rises: the API text is "Set this value longer than the expected cleanup time for your
   process."
2. **An exec-form entry point.** A shell entry point is not a style question here. `/bin/sh -c`
   "does not pass signals", and the whole 30 s then elapses before SIGKILL with the drain never
   having begun. This is the failure most likely to survive review, because the Pod terminates
   *eventually* and the only symptom is that termination always takes exactly the grace period.
3. **A SIGTERM handler registered with `loop.add_signal_handler`.** `asyncio.Runner` handles SIGINT
   and nothing else, and only this registration gives a callback that "is allowed to interact with
   the event loop" and that "will be invoked by *loop*, along with other queued callbacks and
   runnable coroutines of that event loop". Two consequences follow for the drain's own design: the
   handler must be idempotent, because a kubelet restart "retries from the start including the full
   original grace period" — and the same at-least-once posture is stated outright for the one other
   shutdown callback Kubernetes offers, "Hook delivery is intended to be *at least once*", so
   re-entry is the platform's stance on shutdown callbacks generally, not a quirk of one path; and a
   second SIGTERM has no platform-defined meaning, so if a second signal is to mean "stop waiting",
   the application defines that itself.
4. **`.spec.strategy.type: Recreate`, or a StatefulSet, for a workload that must not have two live
   consumers.** The default rolling update creates the replacement before the old Pod is gone.
   `Recreate` fixes the upgrade case only — "If you need an \"at most\" guarantee for your Pods, you
   should consider using a StatefulSet" — and neither removes the need for ADR-0023's
   single-consumer lease, because both are voided by force deletion and by partitions. Choosing
   `Recreate` also retires `maxSurge` and `maxUnavailable` from the manifest: the `rollingUpdate`
   block is "Present only if DeploymentStrategyType = RollingUpdate", so the two rows for them in §8
   stop applying the moment this requirement is met.

Left out deliberately: **no `preStop` hook.** For a Pod that no Service selects there is no
EndpointSlice to propagate out of, the sleep would be charged against the same 30 s, and admission
would cap it at the grace period anyway. Also left out: **no probe-level
`terminationGracePeriodSeconds`**, which governs the probe-failure path and not a delete, and cannot
be set on a readiness probe at all.

Optional and genuinely cheap: **`minReadySeconds`** at something greater than 0, so a revision that
connects and immediately fails does not count as a successful rollout.

**A PDB is not the cheap addition it looks like.** At `replicas: 1`, `minAvailable: 1` is exactly
the zero-eviction case: "If you set `maxUnavailable` to 0% or 0, or you set `minAvailable` to 100%
or the number of replicas, you are requiring zero voluntary evictions", and the documented
consequence is not a wait but a stall — "If you try to drain a Node where an unevictable Pod is
running, the drain never completes." Combining that with requirement 4 above produces the one
operational trap this note can name in advance: the operator who meets a stuck node drain reaches
for `kubectl delete --force`, and force deletion is precisely what voids the guarantee the workload
kind was chosen for — it "can lead to the duplication of a still-running Pod, and if said Pod can
still communicate with the other members of the StatefulSet, will violate the at most one semantics
that StatefulSet is designed to guarantee." So either accept eviction (no PDB, "tolerate occasional
downtime", in the page's own words) or accept that draining the node is a coordinated manual step —
"Have an understanding (outside of Kubernetes) that the cluster operator needs to consult you before
termination… then delete the PDB to indicate readiness for disruption. Recreate afterwards."
Whichever is chosen, ADR-0023's single-consumer lease is what keeps the invariant when the platform
mechanism is forced.

**When the budget is shorter than the drain, the loss is unconditional.** If the drain deadline is
25 s and `terminationGracePeriodSeconds` is 20, the kubelet's behaviour at expiry is "The container
runtime sends `SIGKILL` to any processes still running in any container in the Pod." SIGKILL cannot
be caught: no `finally`, no `CancelledError`, no `DrainTimedOut(count)` report, no final flush, and
no state written. What the kubelet guarantees instead is a floor, and the floor is two seconds:
`killContainer` raises an exhausted budget back to `minimumGracePeriodInSeconds = 2` — "A minimal
shutdown window for avoiding unnecessary SIGKILLs" — immediately before `StopContainer`. Two seconds
is not a drain; the arithmetic is unchanged and `terminationGracePeriodSeconds` still has to exceed
the drain deadline. The documentation's own arithmetic example is the one to copy into the design:
with a 60 s period, a 55 s hook and a 10 s stop, "the Container will be killed
before it can stop normally, since `terminationGracePeriodSeconds` is less than the total time
(55+10)". Two further ways to arrive at a short budget are worth naming: a delete that shortens it
(`deletionTimestamp` "may be shortened", `kubectl delete --grace-period`), and a force deletion,
where "the API server does not wait for confirmation from the kubelet that the Pod has been
terminated on the node it was running on."

## 10 Where the shutdown budget lands for an ASGI host

| Server | Version | Request-drain bound | Default | Lifespan-shutdown bound | Signal mechanism |
|---|---|---|---|---|---|
| uvicorn | 0.52.4 | `--timeout-graceful-shutdown` | **unset — waits without bound** | **none** | `signal.signal`, main thread only |
| granian | 2.8.2 | none for in-flight requests | — | **none** | master: `signal.signal`; workers: `loop.add_signal_handler` (async) / `signal.signal` (sync); SIGINT + SIGTERM |
| hypercorn | 0.18.0 | `graceful_timeout` / `--graceful-timeout` | **3 s** | `shutdown_timeout`, **60 s** | `loop.add_signal_handler`, falling back to `signal.signal` |

The version column is the latest release each project's package index reports; the code quoted below
is each project's default branch, read on 2026-09-10, so a line could in principle post-date the
release named beside it.

**uvicorn.** `--timeout-graceful-shutdown` is `type=int, default=None`, "Maximum number of seconds
to wait for graceful shutdown."; the settings page adds "After this timeout, the server will start
terminating requests." It arrived in 0.22.0 (28 April 2023) as "Add `--timeout-graceful-shutdown`
parameter (#1950)". `Server.shutdown` closes the listening sockets, calls `connection.shutdown()` on
every connection, and then awaits `asyncio.wait_for(self._wait_tasks_to_complete(),
timeout=self.config.timeout_graceful_shutdown)`. **Unset, it waits without bound**:
`asyncio.wait_for` is documented as "If *timeout* is ``None``, block until the future completes." On
expiry it logs "Cancel %s running task(s), timeout graceful shutdown exceeded" and cancels each task
with the message "Task cancelled, timeout graceful shutdown exceeded".

The important part for a bot is what comes *after* that call: `if not self.force_exit: await
self.lifespan.shutdown()`. The ASGI lifespan shutdown is therefore **outside**
`timeout_graceful_shutdown`, and `LifespanOn.shutdown` puts `{"type": "lifespan.shutdown"}` on the
queue and then `await self.shutdown_event.wait()` — with no timeout at all. If the drain runs in the
lifespan shutdown handler, uvicorn imposes no deadline on it whatsoever and the only bound left is
`terminationGracePeriodSeconds` and SIGKILL.

uvicorn's signal handling is a deliberate choice worth recording, because it is the opposite of what
§4 recommends: `HANDLED_SIGNALS` is `SIGINT`, `SIGTERM` (plus `SIGBREAK` on Windows) and the
`capture_signals` context manager comments "always use signal.signal, even if
loop.add_signal_handler is available / this allows to restore previous signal handlers later on",
restoring the originals on exit and re-raising the captured signals in LIFO order afterwards. That
comment is about the *choice* of mechanism, not about installing one unconditionally: the same
method opens with "# Signals can only be listened to from the main thread." followed by `if
threading.current_thread() is not threading.main_thread(): yield; return`, so a uvicorn `Server`
started off the main thread installs no handler at all and its drain never fires. Its
`handle_exit` escalates on a second signal only for SIGINT — `if self.should_exit and sig ==
signal.SIGINT: self.force_exit = True` — so a **second SIGTERM does nothing**, which matches the
platform, since Kubernetes sends one signal and then SIGKILL.

**granian** 2.8.2 exposes no graceful-shutdown timeout for in-flight requests in its CLI. The only
shutdown-shaped option is `--workers-kill-timeout`, `type=Duration(1, 1800)`, "The amount of time in
seconds (or a human-readable duration) to wait for killing workers that refused to gracefully stop",
with `show_default='disabled'`. Its ASGI lifespan shutdown is `await self.event_shutdown.wait()`
after putting `lifespan.shutdown` on the queue — unbounded, like uvicorn's. **[unverified as an
exhaustive statement — established by reading `granian/cli.py` and `granian/asgi.py` and finding no
other timeout; the Rust request-handling core was not read.]**

granian is the one host of the three where the drain does not run in PID 1, so §4's "the signal goes
to PID 1 and nowhere else" needs reconciling with it. Three facts do that, and all three are Python,
not Rust. The master registers its own handlers with
`set_main_signals(self.signal_handler_interrupt, self.signal_handler_reload)`, and
`set_main_signals` loops `signal.signal(sig, interrupt_handler)` over `[signal.SIGINT,
signal.SIGTERM]`; `signal_handler_interrupt` only sets `self.interrupt_signal = True` and
`self.main_loop_interrupt.set()`. The master then stops each worker itself — `_stop_workers` begins
`for wrk in self.wrks: wrk.terminate()`, and `WorkerProcess.terminate` is
`self.inner.terminate()`, a `multiprocessing.Process` method documented as "Terminate the process.
On POSIX this is done using the `SIGTERM` signal". The child catches that with its own handler,
installed by `set_loop_signals` (`loop.add_signal_handler(sigval, signal_handler, sigval, None)`,
falling back to `signal.signal` on `NotImplementedError`) for async workers or `set_sync_signals`
for sync ones — in both cases the handler only does `signal_event.set()`. So the drain does start
under granian: SIGTERM to PID 1 becomes SIGTERM to each worker, and the worker's loop-safe handler
is what fires.

How long the master then waits is the part with no bound. `_stop_workers` computes `timeout =
self.workers_kill_timeout if self.workers_kill_timeout else None` and calls `wrk.join(timeout)`; the
kill escalation is inside `if self.workers_kill_timeout:`. At the default — `disabled` — the timeout
is `None`, `join(None)` blocks until the worker exits, and nothing ever calls `wrk.kill()`. granian
therefore imposes no deadline on a worker's drain at any level, and `terminationGracePeriodSeconds`
is again the only backstop.

**hypercorn** is the only one of the three that bounds both halves, and it documents both.
`graceful_timeout` maps to `--graceful-timeout`, "Time to wait after SIGTERM or Ctrl-C for any
remaining requests (tasks) to complete", default `3s` in the table and
`graceful_timeout: float = 3 * SECONDS` in `Config`. `shutdown_timeout` has no CLI flag and is
"Timeout when waiting for Lifespan shutdowns to complete", `60s`, enforced as
`await asyncio.wait_for(self.shutdown.wait(), timeout=self.config.shutdown_timeout)` raising
`LifespanTimeoutError("shutdown")`. Its shutdown sequence is the same shape as uvicorn's — close
servers, `asyncio.wait_for(gathered_server_tasks, config.graceful_timeout)`, then
`await lifespan.wait_for_shutdown()` — so lifespan shutdown is again outside the request-drain
timeout, only this time it has a bound of its own. Its signal registration prefers the asyncio path:
for each of `SIGINT`, `SIGTERM`, `SIGBREAK` it calls `loop.add_signal_handler`, falling back to
`signal.signal` where that is "not implemented on Windows".

The design consequence is one sentence: **on the two servers most likely to host the probe endpoint,
a drain that runs inside ASGI lifespan shutdown has no server-side deadline at all**, so the drain
must own its own clock — which is what ADR-0023's 25 s grace period is — and the Pod grace period is
the only backstop.

## 11 Peer practice for an outbound-only worker

Six long-lived-consumer projects were read at their published default branches. **Exactly one names
`terminationGracePeriodSeconds`, and none publishes a value for it.**

| Project | Drain control | Default | Signals | Kubernetes artefact |
|---|---|---|---|---|
| `python-arq/arq` | `job_completion_wait` | **`0`** — cancel at once | `loop.add_signal_handler`, SIGINT + SIGTERM | none; names the k8s field in a docstring |
| `celery/celery` | `worker_soft_shutdown_timeout` | **`0.0`** — disabled | TERM warm, QUIT cold, INT escalates | Helm chart Deployment, no drain fields |
| `Bogdanp/dramatiq` | `--worker-shutdown-timeout` | **`600000` ms (10 min)** | `signal.signal`, SIGINT + SIGTERM | none |
| `taskiq-python/taskiq` | `--wait-tasks-timeout`, `--shutdown-timeout` | **`None`**, **`5`** s | `signal.signal`, SIGINT + SIGTERM + SIGHUP | none |
| `ag2ai/faststream` | none — shutdown hooks are unbounded | — | `loop.add_signal_handler`, SIGINT + SIGTERM | Deployment manifest in the docs, no drain fields |
| `slackapi/bolt-python` | none | — | **none** — `Event().wait()` | none |

- **arq** is the only project that connects its own knob to the platform field. Its docstring reads:
  "time to wait before cancelling tasks after a signal. Useful together with
  ``terminationGracePeriodSeconds`` in kubernetes, when you want to make the pod complete jobs
  before shutting down. The worker will not pick new tasks while waiting for shut down." The
  parameter is `job_completion_wait: int = 0`, and the default selects a *different signal handler*:
  with a falsy value the worker registers `handle_sig`, with a truthy one
  `handle_sig_wait_for_completion`, which sets `allow_pick_jobs = False` and then
  `asyncio.wait_for(self._sleep_until_tasks_complete(), self._job_completion_wait)` before
  cancelling what is left. At the default there is no drain. No number is recommended anywhere.
- **celery** has the richest vocabulary and the emptiest default. "When the worker receives the
  `TERM` signal, it will initiate a warm shutdown. The worker will finish all currently executing
  tasks before it actually terminates", and "Additional `TERM` signals will be ignored during the
  warm shutdown process." The time-limited variant added in 5.5 is off: "The soft shutdown is
  disabled by default to maintain backward compatibility with the cold shutdown behavior. To enable
  the soft shutdown, set `worker_soft_shutdown_timeout` to a positive float value." The defaults
  file confirms `soft_shutdown_timeout=Option(0.0, type='float')` and
  `enable_soft_shutdown_on_idle=Option(False, type='bool')`. One trap is documented and would break
  a Kubernetes drain outright: "If the environment variable ``REMAP_SIGTERM`` is set to ``SIGQUIT``,
  the worker will also initiate a cold shutdown when it receives the `TERM` signal instead of a warm
  shutdown." Celery's Helm chart contains a Deployment template with no
  `terminationGracePeriodSeconds`, no `preStop` and no `strategy`.
- **dramatiq** ships the only generous default in the set — `--worker-shutdown-timeout`,
  `default=600000`, "timeout for worker shutdown, in milliseconds (default: 10 minutes)" — which is
  twenty times the Pod default and therefore a number that can only ever be cut short by SIGKILL
  under Kubernetes.
- **taskiq** splits the budget: `--wait-tasks-timeout` is "Maximum time to wait for all current
  tasks to finish before exiting." with `default=None`, and `--shutdown-timeout` is "Maximum amount
  of time for graceful broker's shutdown is seconds." with `shutdown_timeout: float = 5`, applied as
  `asyncio.wait_for(broker.shutdown(), timeout)` and logged as "Broker.shutdown cannot be completed
  in %s seconds." on expiry. It is also the only project with an escalation counter:
  `hardkill_count: int = 3`, and the handler raises `KeyboardInterrupt` once
  `hardkill_counter > args.hardkill_count`.
- **FastStream** registers the signals the right way and then bounds nothing. `FastStream.run` calls
  `set_exit(lambda *_: self.exit(), sync=False)`, which registers `SIGINT` and `SIGTERM` through
  `loop.add_signal_handler` and falls back to `signal.signal` only in sync or Windows mode; the
  handler sets `_should_exit`, a `while not self._should_exit: await anyio.sleep(sleep_time)` loop
  with `sleep_time: float = 0.1` notices, and `_shutdown` then runs the broker close and the
  `on_shutdown`/`after_shutdown` hooks with **no timeout around them**. Its published Kubernetes
  Deployment — `replicas: 1`, a liveness probe on `/internal/alive` with `initialDelaySeconds: 5`
  and `periodSeconds: 20`, a readiness probe on `/internal/ready` with `periodSeconds: 60` — sets
  **no** `terminationGracePeriodSeconds`, **no** `preStop` and **no** `strategy`, and its container
  runs `command: ["/bin/sh", "-c", 'python3 main.py']`, the shell form §4 warns about.
- **bolt-python** has no drain at all. `SocketModeHandler.start()` connects and then blocks on
  `Event().wait()`, and the adapter's only signal code is `signal.signal(signal.SIGINT,
  signal.SIG_DFL)` guarded by `sys.platform == "win32"`. Nothing handles SIGTERM.

**What none of them documents**: a `terminationGracePeriodSeconds` value, the relationship between
their own timeout and the Pod grace period, or what happens when the two disagree. (Negative
established by searching all six repositories for the literal string
`terminationGracePeriodSeconds` —
one hit, the arq docstring above — and for `kind: Deployment` — two hits, the celery Helm template
and the FastStream documentation page.)

## 12 What the evidence supports

- **A graceful drain depends on two Kubernetes fields and two things Kubernetes cannot set.**
  `terminationGracePeriodSeconds` and the workload kind with its `.spec.strategy.type` are the
  platform's contribution; the exec-form entry point and the SIGTERM handler live in the image and
  the process. A design that only sets the manifest fields has fixed half of it.
- **The grace period is not a SIGTERM timer.** The countdown "begins before the `PreStop` hook is
  executed" and covers "the total time it takes for both the `PreStop` hook to execute and for the
  Container to stop normally". A 25 s drain inside a 30 s budget has 5 s of margin for everything
  else, and any `preStop` sleep comes out of that 5 s.
- **The documented "2 second extension" is a floor, not a reprieve.** `killContainer` raises an
  exhausted budget back to `minimumGracePeriodInSeconds = 2` — "A minimal shutdown window for
  avoiding unnecessary SIGKILLs" — before calling `StopContainer`, so every container gets 2 s of
  stop window whatever the arithmetic produced. Two seconds is not 25; a short budget still loses
  the drain.
- **A `preStop` *sleep* is an endpoint-propagation tool and this workload has no endpoints.** Every
  documented purpose of a sleep — KEP-3960's motivation included — is about giving a load balancer
  or service mesh time to stop sending traffic. `preStop` itself is additionally documented for
  saving state and for shutdown ordering, and this design needs neither: the drain runs in-process.
  A hook would also add a kill path — "If either a `PostStart` or `PreStop` hook fails, it kills the
  Container." Omit it.
- **Liveness cannot interfere with a drain, and readiness keeps being asked but nobody listens.**
  The probe worker forces `results.Success` for liveness and startup as soon as `deletionTimestamp`
  is set, and the manager stops those workers before `killPod`. Readiness alone survives —
  "Readiness probes run on the container during its whole lifecycle." — but for a Pod no Service
  selects, `FilterActivePods`, `canIgnorePDB` and the Service-selector requirement between them
  leave no consumer for an answer given after the delete request. Readiness paces the rollout; it
  does not pace the drain.
- **A PodDisruptionBudget guards the decision to start draining, not the drain — and at one replica
  it does not even do that safely.** `canIgnorePDB` returns true the moment `deletionTimestamp` is
  set, after which only the grace period stands between the process and SIGKILL. At `replicas: 1`,
  `minAvailable: 1` is the zero-eviction case, so "the drain never completes", and the force
  deletion that unsticks it is exactly what voids the StatefulSet at-most-one guarantee.
- **No workload kind removes the need for an application-level lease.** `Recreate` bounds upgrades
  only; the StatefulSet "at most one" guarantee is stated for a Pod identity and is explicitly
  voided by force deletion. ADR-0023's single-consumer lease is the mechanism that survives both.
- **The ASGI hosts do not bound a drain that runs in lifespan shutdown.** uvicorn's
  `timeout_graceful_shutdown` covers connections and background tasks and stops before
  `lifespan.shutdown()`, which then waits on an event with no timeout; granian is the same shape,
  and its master waits on `wrk.join(None)` at the default because `--workers-kill-timeout` is
  `disabled`; only hypercorn bounds lifespan shutdown, at 60 s. The drain must own its own clock.
  Two host-specific traps go with that: uvicorn installs no signal handler at all off the main
  thread ("# Signals can only be listened to from the main thread."), and under granian the drain
  runs in a spawned worker that receives SIGTERM from the master's `Process.terminate()`, not from
  the kubelet.
- **The ecosystem default is no drain.** arq waits 0 s, celery's soft shutdown is disabled, taskiq
  waits `None`, FastStream bounds its shutdown hooks not at all, bolt-python has no SIGTERM handler,
  and dramatiq's 10-minute default is twenty times longer than the Pod grace period. Only arq
  mentions `terminationGracePeriodSeconds`, and it publishes no number. There is no peer practice to
  copy — the numbers have to come from the Kubernetes documentation, which is what this note is
  for.

## Sources

Kubernetes concepts and tasks:

- <https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination> · <https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/> · <https://kubernetes.io/docs/concepts/workloads/pods/probes/>
- <https://kubernetes.io/docs/concepts/workloads/controllers/deployment/> · <https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/> · <https://kubernetes.io/docs/tasks/run-application/force-delete-stateful-set-pod/>
- <https://kubernetes.io/docs/concepts/workloads/pods/disruptions/> · <https://kubernetes.io/docs/tasks/run-application/configure-pdb/> · <https://kubernetes.io/docs/tutorials/services/pods-and-endpoint-termination-flow/>
- <https://kubernetes.io/docs/concepts/cluster-administration/node-shutdown/> · <https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/> · <https://kubernetes.io/docs/reference/kubectl/generated/kubectl_delete/>
- <https://kubernetes.io/docs/reference/kubernetes-api/workload-resources/deployment-v1/>
- <https://github.com/kubernetes/website/blob/main/content/en/docs/reference/command-line-tools-reference/feature-gates/PodLifecycleSleepAction.md> · <https://github.com/kubernetes/website/blob/main/content/en/docs/reference/command-line-tools-reference/feature-gates/PodLifecycleSleepActionAllowZero.md> · <https://github.com/kubernetes/website/blob/main/content/en/docs/reference/command-line-tools-reference/feature-gates/ContainerStopSignals.md>
- <https://github.com/kubernetes/enhancements/blob/master/keps/sig-node/3960-pod-lifecycle-sleep-action/README.md>

Kubernetes API and kubelet source:

- <https://github.com/kubernetes/kubernetes/blob/master/staging/src/k8s.io/api/core/v1/types_swagger_doc_generated.go> · <https://github.com/kubernetes/kubernetes/blob/master/staging/src/k8s.io/apimachinery/pkg/apis/meta/v1/types_swagger_doc_generated.go>
- <https://github.com/kubernetes/kubernetes/blob/master/pkg/apis/core/validation/validation.go> · <https://github.com/kubernetes/kubernetes/blob/master/pkg/registry/core/pod/storage/eviction.go>
- <https://github.com/kubernetes/kubernetes/blob/master/pkg/kubelet/kubelet.go> · <https://github.com/kubernetes/kubernetes/blob/master/pkg/kubelet/prober/prober_manager.go> · <https://github.com/kubernetes/kubernetes/blob/master/pkg/kubelet/prober/worker.go> · <https://github.com/kubernetes/kubernetes/blob/master/cmd/kubelet/app/options/options.go>
- <https://github.com/kubernetes/kubernetes/blob/master/pkg/kubelet/kuberuntime/kuberuntime_container.go> · <https://github.com/kubernetes/kubernetes/blob/master/pkg/kubelet/kuberuntime/kuberuntime_manager.go> · <https://github.com/kubernetes/kubernetes/blob/master/pkg/controller/controller_utils.go>

Containers and the language:

- <https://docs.docker.com/reference/dockerfile/>
- <https://docs.python.org/3/library/asyncio-eventloop.html> · <https://docs.python.org/3/library/asyncio-runner.html> · <https://docs.python.org/3/library/asyncio-task.html> · <https://docs.python.org/3/library/signal.html> · <https://docs.python.org/3/library/multiprocessing.html>

ASGI hosts:

- <https://github.com/encode/uvicorn/blob/main/uvicorn/server.py> · <https://github.com/encode/uvicorn/blob/main/uvicorn/main.py> · <https://github.com/encode/uvicorn/blob/main/uvicorn/lifespan/on.py> · <https://github.com/encode/uvicorn/blob/main/docs/settings.md> · <https://github.com/encode/uvicorn/blob/main/docs/release-notes.md>
- <https://github.com/emmett-framework/granian/blob/master/granian/cli.py> · <https://github.com/emmett-framework/granian/blob/master/granian/asgi.py> · <https://github.com/emmett-framework/granian/blob/master/granian/server/mp.py> · <https://github.com/emmett-framework/granian/blob/master/granian/server/common.py> · <https://github.com/emmett-framework/granian/blob/master/granian/_signals.py> · <https://pypi.org/pypi/granian/json>
- <https://github.com/pgjones/hypercorn/blob/main/src/hypercorn/config.py> · <https://github.com/pgjones/hypercorn/blob/main/src/hypercorn/asyncio/run.py> · <https://github.com/pgjones/hypercorn/blob/main/src/hypercorn/asyncio/lifespan.py> · <https://github.com/pgjones/hypercorn/blob/main/docs/how_to_guides/configuring.rst> · <https://pypi.org/pypi/Hypercorn/json>

Peer workers:

- <https://github.com/python-arq/arq/blob/main/arq/worker.py>
- <https://github.com/celery/celery/blob/main/docs/userguide/workers.rst> · <https://github.com/celery/celery/blob/main/celery/app/defaults.py> · <https://github.com/celery/celery/blob/main/helm-chart/templates/deployment.yaml>
- <https://github.com/Bogdanp/dramatiq/blob/master/dramatiq/cli.py>
- <https://github.com/taskiq-python/taskiq/blob/master/taskiq/cli/worker/args.py> · <https://github.com/taskiq-python/taskiq/blob/master/taskiq/cli/worker/run.py>
- <https://github.com/ag2ai/faststream/blob/main/docs/docs/en/getting-started/observability/healthcheks.md> · <https://github.com/ag2ai/faststream/blob/main/faststream/app.py> · <https://github.com/ag2ai/faststream/blob/main/faststream/_internal/cli/supervisors/utils.py>
- <https://github.com/slackapi/bolt-python/blob/main/slack_bolt/adapter/socket_mode/base_handler.py>
