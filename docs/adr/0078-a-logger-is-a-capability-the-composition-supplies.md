---
status: accepted
date: 2026-09-14
ticket: "#103"
amends: [ADR-0053]
---

# A logger arrives like every other capability, typed `logging.Logger | None`, and the framework owns no logger Protocol

`ST-LOG-01` names one logger per component `aiommbot.<component>` and admits no exceptions, which
answers nothing for a third-party Plugin that is not `aiommbot.*`, and
[ADR-0070](0070-plugins-do-not-collaborate-the-composition-hands-one-instance-to-both.md) had
already fixed the channel for anything a Plugin consumes: its typed frozen settings. A logger is
such a capability, so it arrives the same way.

- **The parameter is `logger: logging.Logger | None = None`, and `None` means the object builds its
  own.** That is **websockets'** exact shape — the parameter is on the sans-I/O base, defaults to
  `None` at every layer, and the default name is built per unit. It exists wherever the application
  constructs the object: a Plugin's settings type and the Bot's own. A Core component the Bot builds
  for itself — the Dispatcher, the Router, the ErrorBoundary — takes no such parameter and keeps its
  name.
- **The type is the standard library's `Logger`, and the framework owns no logger Protocol.** The
  reason a Protocol is usually reached for is structlog, and the measurement removes it:
  `structlog.get_logger()` is typed `Any` and its own documentation says so, so both mypy `--strict`
  and ty already accept it where `logging.Logger` is required
  ([`docs/research/43`](../research/43-who-owns-a-librarys-logger.md)).
- **Handing a structlog logger in would break the record contract anyway.** `extra=` passed *into*
  one never reaches a record: the default configuration renders it into the message text, and
  `render_to_log_kwargs` re-nests it as `extra["extra"]`. Correlation
  ([ADR-0054](0054-correlation-reaches-a-log-record-in-three-layers.md)) and the redaction list
  ([ADR-0055](0055-one-redaction-list-over-two-sinks.md)) both ride on `extra` field names.
  structlog's own advice to a library is the section titled **"Don't integrate"** — configure
  standard-library logging and attach `ProcessorFormatter`, whose `ExtraAdder` lifts exactly our
  `extra` fields into the event dictionary. The compatibility is the application's to arrange, and
  it arrives in the shape we already write.
- **A narrow Protocol loses four things the field uses.** `isEnabledFor` — websockets, httpcore,
  aiohttp, redis-py and sqlalchemy all guard on it; `%`-lazy `*args`; `.exception()`; and
  `stacklevel`, whose loss is not theoretical — FastStream's proxy does not forward it, so every
  record it writes reports the proxy's own line instead of the call site, which is the same defect
  structlog subclasses `logging.Logger` to fix.
- **The standard-library annotation is what protects a loguru user**, which is the opposite of the
  usual argument for a Protocol. `loguru.logger` is a bare class, not a `logging.Logger`, and a
  stdlib-shaped call on it silently nests `extra` one level deeper — so correlation and the
  redaction list, which match on `extra` field names, would find nothing — and raises outright if
  the constant message contains a brace. A one-method Protocol would admit that object and fail; the
  `logging.Logger` annotation refuses it at type-check time, and loguru's own `InterceptHandler`
  seam is where loguru's documentation puts a library's records anyway
  ([`docs/research/43`](../research/43-who-owns-a-librarys-logger.md)).
- **No new seam, and no fifteenth conformance suite.** [§5.4](../design/05-building-block-view.md)
  stays thirteen rows and [ADR-0047](0047-a-conformance-suite-per-core-seam.md) fourteen suites. A
  logger Protocol has no conformance test anywhere in seventy-six projects, and CPython declines to
  make its own logger check `runtime_checkable`.
- **Two states, not three.** FastStream needs a third — a sentinel so that `None` can mean silence —
  because it configures logging itself. We do not
  ([ADR-0053](0053-log-records-are-a-documented-contract.md)), so silence is what it has always
  been: the application's own configuration over a name it can see.

## Considered options

- *A one-method Protocol, FastStream's `LoggerProto`* — rejected on its measured cost above. Its
  structlog compatibility rests on a single `/` making the parameters positional-only, untested
  anywhere; tenacity's near-identical Protocol omits that character and its docstring claim of
  structlog compatibility is refuted by a type checker.
- *A nine-member Protocol, Litestar's `Logger`* — rejected: it declares nine members, calls one, and
  encodes its real requirement — that the logger accept arbitrary keyword arguments — in a boolean
  parameter rather than in the type, so a checker accepts a combination that raises at runtime.
  Litestar 3.0 deleted its whole logging layer and told users to configure standard-library logging
  instead.
- *The union `logging.Logger | LoggerAdapter`, websockets' literal type* — rejected: `LoggerAdapter`
  is already banned by [ADR-0054](0054-correlation-reaches-a-log-record-in-three-layers.md) because
  it drops per-call `extra` below Python 3.13 and our floor is 3.12.
- *A sentinel and a null-logger object, so `logger=None` means silence* — rejected: it buys a state
  we do not need, since we never take the application's logging configuration away from it.

## Consequences

- [ADR-0053](0053-log-records-are-a-documented-contract.md) said the framework offers no logging
  helper. It still ships none — no factory, no configuration, no handler beyond `NullHandler` — and
  now also accepts one, which is the opposite direction and is stated there.
- What a third-party Plugin names the logger it builds when none is supplied, and what of
  `ST-LOG-01` and `ST-LOG-08` binds it, is
  [ADR-0079](0079-the-record-catalogue-survives-a-supplied-logger.md)'s.
- `logger` is a field of a public frozen dataclass, so its name is public on the terms of
  [ADR-0077](0077-a-field-of-a-public-frozen-dataclass-is-a-public-name.md) like any other.
