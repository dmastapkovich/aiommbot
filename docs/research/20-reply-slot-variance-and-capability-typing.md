# 20. Reply-slot variance and capability typing

**Question.** The immutable generic envelope `Event[P, R = Never]` carries an optional typed Reply
channel `meta.reply: ReplyChannel[R] | None`, where `ReplyChannel[R]` is a Core-owned Protocol with
`async def send(self, reply: R) -> None | ReplyAlreadySent`. How should that be spelled so that
(1) `Event[InteractiveAction, ActionReply]` is assignable where a Handler annotates
`Event[InteractiveAction]`, (2) `derive` keeps the guarantee of
[ADR-0037](../adr/0037-derive-is-the-only-enrichment-path-for-an-event.md) (payload and kind
untouched), (3) mypy, pyright, pyrefly and ty all agree, and (4) the type stays cheap to maintain
when a third parameter is added? Two side questions: where does the fieldless typed-outcome marker
`ReplyAlreadySent` live without a Core → plugin import, and how do strictly typed Python libraries
model a capability handed to user code with a type parameter?

Gathered for the `Event` component document. Findings only — the decisions are ADR-0036 and
ADR-0037, which §Recommendation says how to amend. Every checker claim below was run on
2026-09-08 with **mypy 2.3.1**, **pyright 1.1.411**, **pyrefly 1.2.0** and **ty 0.0.79**
(`typing_extensions` 4.16.0), each once in `--python-version 3.13` mode (native PEP 695/696
syntax) and once in `3.12` mode (the floor of
[ADR-0008](../adr/0008-python-floor-3-12-with-typing-extensions.md)). Library claims come from the
default branch of each repository read on the same day. Anything not checked is marked
**[unverified]**.

## 1 Variance: what the checkers actually infer

### 1.1 The theory, and why the current spelling cannot be contravariant

Contravariance is the right target: for a contravariant `R`, `Event[IA, ActionReply]` is a subtype
of `Event[IA, Never]` because `Never` is a subtype of `ActionReply` (bottom type — "the empty set of
Python objects", [typing spec, *Never*](https://typing.python.org/en/latest/spec/special-types.html#never)).
With the PEP 696 default `R = Never`, `Event[IA]` is then the *top* of the `R` lattice: any slotted
envelope is assignable to it, and `send` on its slot demands an argument of type `Never`, which no
expression has — the "uncallable `send`" of ADR-0036 is a consequence, not a separate rule.

Under PEP 695 the variance of a type parameter is inferred, not declared. The spec's algorithm
builds two specialisations, `upper` (`object`) and `lower` (`Never`), and asks whether one is
assignable to the other "using normal assignability rules"
([spec, *Variance Inference*](https://typing.python.org/en/latest/spec/generics.html#variance-inference)).
Any member whose signature takes `R` in an input position blocks the contravariant answer. In
`class Event[P, R = Never]` two members do:

- `def derive(self, *, meta: EventMeta[R]) -> Event[P, R]` — `EventMeta[R]` in a parameter. Since
  `EventMeta` itself is contravariant in `R`, the parameter position flips it into a *covariant* use;
  together with the contravariant use in the `meta` field, `R` is invariant. This is the defect the
  question names, and every checker reproduces it (table below, row *A*).
- On Python 3.13 the dataclass decorator synthesises `__replace__(self, *, kind=…, payload=…,
  meta: EventMeta[R]) -> Self`. That is a second input position for `R`, and — decisive for the
  design — it is present **even after `derive` is fixed**. The frozen field alone is not enough:
  pyright and ty infer a frozen dataclass with one field `reply: ReplyChannel[R] | None` as
  *invariant* in 3.13 mode and *contravariant* in 3.12 mode (probe `M3`, table §1.3). The cause is
  documented upstream: "the synthesized `__replace__` method … takes `T` in parameter position"
  ([discuss.python.org, *Make `__replace__` stop interfering with variance inference*, June–August
  2025, no consensus](https://discuss.python.org/t/make-replace-stop-interfering-with-variance-inference/96092);
  [pyright discussion #11012](https://github.com/microsoft/pyright/discussions/11012);
  [pyright issue #9241](https://github.com/microsoft/pyright/issues/9241)). Mypy ignores
  `__replace__` for inference and accepts the frozen field as read-only, which is why mypy alone
  passes variant *B*. PEP 767 would make frozen-dataclass attributes "implied to be read-only" and
  therefore covariant-safe, but it is a **Draft** targeting 3.15
  ([PEP 767](https://peps.python.org/pep-0767/)).

There is a second, independent reason the PEP 695 spelling is unavailable: the floor is 3.12, and
the `R = Never` default in a type-parameter list is 3.13 syntax. Both pyright ("Type variable default
types require Python 3.13 or newer") and ty ("Cannot set default type for a type parameter on Python
3.12") reject `class Event[P, R = Never]` in 3.12 mode. On the floor, `Event` must be written
`class Event(Generic[P, R])` with `R = TypeVar("R", default=Never, …)` from `typing_extensions`
— which is the compat module ADR-0008 already provides for. And on that old-style `TypeVar`,
`infer_variance=True` is rejected by mypy 2.3.1 with `Unexpected argument to "TypeVar()":
"infer_variance"` ([python/mypy#20313](https://github.com/python/mypy/issues/20313), open) — so
the variance of `R` has to be declared, not inferred, whatever we might prefer.

### 1.2 The five candidates under four checkers

Snippets: a shared `common.py` (payloads, `ActionReply`, `DialogReply`, `ReplyAlreadySent`,
`ReplyChannel[R]`) and one module per variant with the same seven checks:

| # | Check | Expected |
|---|---|---|
| T1 | `widened: Event[IA] = e_slot` (`e_slot: Event[IA, ActionReply]`) | accepted |
| T2 | `narrowed: Event[IA, ActionReply] = e_plain` | rejected |
| T3 | `await handler(e_slot)` with `handler(event: Event[IA])` | accepted |
| T3b | `await slot_handler(e_plain)` with `slot_handler(event: Event[IA, ActionReply])` | rejected |
| T4 | `assert_type(e_slot.derive(meta=replace(e_slot.meta, seq=7)), Event[IA, ActionReply])` | accepted |
| T4b | `e_slot.derive(payload=…)` | rejected |
| T5 | `await e_slot.meta.reply.send(ActionReply())` / `.send(DialogReply())` | accepted / rejected |
| T6 | `assert_type(e_posted.meta.reply, ReplyChannel[Never] \| None)`; `.send(ActionReply())` | accepted; rejected |

A cell is **pass** when exactly the expected diagnostics appear.

| Variant (signature) | mypy 2.3.1 | pyright 1.1.411 | pyrefly 1.2.0 | ty 0.0.79 | `derive` keeps P/kind | Maintainability |
|---|---|---|---|---|---|---|
| **A** — as written: `class Event[P, R = Never]`, `derive(*, meta: EventMeta[R]) -> Event[P, R]` | **fail** T1, T3 (invariant) | **fail** T1, T3 | **fail** T1, T3 (+ spurious `bad-return` on the constructor call, see §1.3) | **fail** T1, T3 | yes (T4b rejected everywhere) | 3.13-only syntax; not usable on the floor |
| **B** — (a) `derive[R2](self, *, meta: EventMeta[R2]) -> Event[P, R2]` | pass (contravariant); also accepts `Event[Posted].derive(meta: EventMeta[ActionReply]) -> Event[Posted, ActionReply]` | **fail** T1, T3 (`__replace__`) | **fail** T1, T3 | **fail** T1, T3 (`__replace__`) | yes | lets a Middleware *change* `R`, i.e. attach or drop the slot through `derive` — a new power ADR-0037 did not grant |
| **C** — (b) explicit `R = TypeVar("R", contravariant=True, default=Never)`, `Generic[P, R]`, `derive(*, meta: EventMeta[R])` | pass | pass | pass (+ spurious `bad-return`) | T1–T6 pass, **but** `error[invalid-generic-class] Variance of type variable R_contra is incompatible with method derive` | yes | declared variance; ty proves the `derive` signature is inconsistent with it |
| **C′** — (b)+(a): explicit contravariant `R`, `derive(self, *, meta: EventMeta[R2]) -> Event[P, R2]` with a plain `R2` | **pass** | **pass** | **pass** | **pass** | yes | the only shape all four accept in **both** 3.12 and 3.13 mode; see §Recommendation for what `R2` means |
| **D** — (c) keep invariance, add `without_reply(self) -> Event[P]` | invariant as designed; T1/T3 rejected, `handler(e_slot.without_reply())` accepted | same | same | same, plus: `replace(self.meta, reply=None)` still has type `EventMeta[R]`, so the narrowing must rebuild `EventMeta[Never]` field by field | yes | the Dispatcher (or every Handler author) must call the widening; rebuilding `EventMeta` duplicates its field list — the objection ADR-0037 raised against `derive(**fields)` |
| **E** — (d) `Event[P]` single-parameter, `ReplyChannel[R]` as a separate Handler parameter | pass (nothing to widen) | pass | pass | pass | yes | **loses the P↔R binding of ADR-0024**: `slot_handler(event: Event[Posted], reply: ReplyChannel[ActionReply])` type-checks in all four; only the DI can reject it at start-up. Also contradicts ADR-0012/0019 (slot invisible to Inbound middleware) — the option ADR-0036 already rejected |

Observations that do not fit the cells:

- **T5/T6 hold in every variant and every checker**: `send(DialogReply())` on an `ActionReply` slot
  and `send(ActionReply())` on a `Never` slot are rejected by all four. The Protocol side of
  ADR-0036 is sound as written; only the envelope's variance was wrong.
- **T4b holds everywhere**: `derive(payload=…)` is a `call-arg`/`unknown-argument` error in all
  four, so ADR-0037's guarantee is a signature fact independent of the variance question.
- **`Never` as default is honoured by all four** (`assert_type(e_posted.meta.reply,
  ReplyChannel[Never] | None)` passes), through both the 3.13 syntax and `typing_extensions.TypeVar(default=Never)`.

### 1.3 Which read-only shapes each checker infers as contravariant

Probes `M1`–`M4`, `Plain`, `Meta` (a single field or property of type `ReplyChannel[R] | None`):

| Shape (PEP 695 syntax) | mypy | pyright | pyrefly | ty |
|---|---|---|---|---|
| the Protocol itself: `class Sink[R](Protocol): async def send(self, reply: R)` | contravariant | contravariant | contravariant | contravariant |
| frozen dataclass field `s: Sink[R]`, 3.12 mode | contravariant | contravariant | **invariant** | contravariant |
| frozen dataclass field `s: Sink[R]`, 3.13 mode | contravariant | **invariant** (`__replace__`) | **invariant** | **invariant** (`__replace__`) |
| read-only `@property` returning `Sink[R]`, either mode | contravariant | contravariant | **invariant** | contravariant |
| `Final[Sink[R]]` attribute | rejects the shape: `Final name declared in class body cannot depend on type variables` | contravariant | **invariant** | contravariant |
| explicit `contravariant=True` on an old-style `TypeVar` | honoured | honoured | honoured | honoured, plus a consistency check on every method |

Pyrefly's column is the odd one: its documentation says it "infers the variance automatically based
on how each type parameter is used" and gives a `Final[T]` covariance example
([pyrefly docs](https://pyrefly.org/en/docs/typing-for-python-developers/)). In 1.2.0 the Protocol
row is inferred correctly, but every class that merely *holds* a `Sink[R]` member — through a frozen
field, a property or `Final` — comes out invariant in both modes. Whether that is a bug in
propagating the variance of a nested generic member is **[unverified]**; the practical reading is
the same as for the others — declared variance is what survives all four. Pyrefly also reports a
spurious `bad-return` on `Event(kind=…, payload=…, meta=meta)` inside `derive` when `R` has a
default (it applies the default instead of solving `R` from `meta`); the report disappears in
variant C′.

## 2 Marker ownership: where `ReplyAlreadySent` lives

The Core Protocol names `ReplyAlreadySent` in a return annotation. With `TYPE_CHECKING` imports
banned (ADR-0006 tenet 7) that annotation is a real import, and
[ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md) forbids the Core to
import from an adapter-specific Plugin. ADR-0035's "markers order nothing" clause is about the
*writing order of documents*, not about the import graph; ADR-0036 leaned on it to leave the value
in `webhook.md`, which the import-linter contract would reject on day one.

What the pattern is called:

- **Not Null Object.** refactoring.guru's catalogue has no Null Object pattern; it lists "Introduce
  Null Object" only as a refactoring under *Simplifying Conditional Expressions*
  ([catalogue](https://refactoring.guru/design-patterns/catalog)). Null Object is a do-nothing
  *implementation of an interface* that removes a branch; `ReplyAlreadySent` exists to *create* a
  branch in the caller.
- **Not Command.** refactoring.guru's Command encapsulates an operation as an object; the catalogue
  says nothing about a typed return value ([catalogue](https://refactoring.guru/design-patterns/catalog)).
- **It is one unit variant of a closed union** — in this project's vocabulary, a Typed outcome
  (CONTEXT.md: "a closed union of frozen, domain-named values a component returns when its immediate
  caller must branch on the result"). Python's own name for a fieldless, singleton-typed union member
  is a *sentinel*: PEP 661 (Final, 3.15) motivates a dedicated sentinel type precisely because an
  `object()` sentinel "does not have a distinct type, hence it is impossible to define clear type
  signatures", and its sentinel is usable as its own type in a union
  ([PEP 661](https://peps.python.org/pep-0661/); a `typing_extensions` backport exists whose
  behaviour "does not precisely match" the final PEP). A frozen fieldless dataclass is the same idea
  spelled with today's stdlib.

Where libraries place such values — next to the interface that names them, never in the
implementation:

| Library | Interface | Value it names | Where the value is defined | Implementation imports it? |
|---|---|---|---|---|
| Trio | `trio.abc.SendChannel[SendType]` (`src/trio/_abc.py`) | `WouldBlock`, `EndOfChannel`, `BrokenResourceError`, `ClosedResourceError` | `trio._core` | yes — `src/trio/_channel.py` imports `BrokenResourceError` from `._core` and uses `trio.EndOfChannel`, `trio.WouldBlock` |
| AnyIO | `anyio.abc.ObjectSendStream[T_contra]` (`src/anyio/abc/_streams.py`) | `EndOfStream`, `WouldBlock`, `BrokenResourceError`, `ClosedResourceError` | `anyio._core._exceptions` | yes — `src/anyio/streams/memory.py`: `from .._core._exceptions import BrokenResourceError, ClosedResourceError, EndOfStream, WouldBlock` |
| django-modern-rest | `dmr.controller.Controller` | error vocabulary in `dmr/exceptions.py`, `dmr/errors.py` | the **base layer** of its `.importlinter` layered contract ("settings and exceptions at the base") | every layer above |
| stdlib | `typing`/`types` | `NotImplemented` (`types.NotImplementedType`) | builtins, next to the operator protocol it serves | — |

Those libraries model the outcome as an *exception*; ADR-0034 makes "already answered" a returned
value instead, but the placement rule is identical: the vocabulary a seam names is owned by the
layer that owns the seam.

## 3 Precedent: a typed capability handed to user code

| Library | Type handed to user code | Parameters, variance | Defaults | How it stays assignable |
|---|---|---|---|---|
| Litestar (`litestar/connection/base.py`, `request.py`, `main`) | `Request(Generic[UserT, AuthT, StateT], ASGIConnection["HTTPRouteHandler", UserT, AuthT, StateT])` | three plain `TypeVar`s (`StateT` bound to `State`), all **invariant**, old-style syntax | **none** | the documentation annotates guards and handlers with bare `ASGIConnection` / `Request` ([guards docs](https://docs.litestar.dev/latest/usage/security/guards.html)); the spec makes a bare generic `Any` in every position ([spec](https://typing.python.org/en/latest/spec/generics.html#user-defined-generic-types)), so assignability is bought with `Any`, not variance |
| Starlette (`starlette/requests.py`, `main`) | `Request(HTTPConnection[StateT])` | one `TypeVar`, invariant | `StateT = TypeVar("StateT", bound=Mapping[str, Any] \| State, default=State)` from `typing_extensions` below 3.13 | a **PEP 696 default** on an old-style `TypeVar` — the same compat spelling this note recommends; `user`/`auth` are `Any` |
| Trio (`src/trio/_abc.py`, `_channel.py`) | `MemorySendChannel[SendType]` implementing `SendChannel[SendType]` | `SendType = TypeVar("SendType", contravariant=True)`, `ReceiveType … covariant=True` — **explicit**, old-style | none | declared variance; `MemorySendChannel` is `@final @attrs.define(eq=False, repr=False, slots=False)` |
| AnyIO (`src/anyio/abc/_streams.py`, `streams/memory.py`) | `MemoryObjectSendStream[T_contra]` | `T_contra = TypeVar("T_contra", contravariant=True)` — **explicit** | none | declared variance; implementation is `@dataclass(eq=False)` |
| django-modern-rest (`dmr/components.py`, `dmr/controller.py`) | `Body[T]`, `Query[T]`, `Headers[T]`… | not generic classes at all: `Annotated[_BodyT, BodyComponent()]` aliases over plain `TypeVar`s; `Controller(View, Generic[_SerializerT_co])` with an **explicit** `covariant=True` | none | the container is an annotation marker, so no variance question arises; the one real generic declares its variance |

Two regularities. Every strictly typed library that hands out a *send*-shaped capability declares
`contravariant=True` explicitly (Trio, AnyIO); none relies on inference. And the only peer with a
defaulted parameter (Starlette) reaches for `typing_extensions.TypeVar(default=…)` — PEP 696 is the
one mechanism Python offers for "add a parameter without touching existing annotations": a
`TypeVarTuple` is always invariant ([spec, *Variance Inference*, step 1](https://typing.python.org/en/latest/spec/generics.html#variance-inference))
and Python has no keyword type arguments. Defaults must trail non-defaulted parameters
([spec, *Defaults for type parameters*](https://typing.python.org/en/latest/spec/generics.html#defaults-for-type-parameters)),
so a third parameter goes after `R` and also needs a default.

## Recommendation

**Adopt variant C′: declare `R` contravariant on the compat `TypeVar`, and let `derive` be typed
by the `EventMeta` it receives.**

```python
# TypeVar is the typing_extensions one re-exported by the compat module (ADR-0008)
P = TypeVar("P")
R = TypeVar("R", contravariant=True, default=Never)
R2 = TypeVar("R2")   # used by derive only

class ReplyChannel(Protocol[R]):
    @property
    def sent(self) -> bool: ...
    @property
    def deadline(self) -> float: ...
    async def send(self, reply: R) -> None | ReplyAlreadySent: ...

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class EventMeta(Generic[R]):
    ...
    reply: ReplyChannel[R] | None

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Event(Generic[P, R]):
    kind: str
    payload: P
    meta: EventMeta[R]

    def derive(self, *, meta: EventMeta[R2]) -> Event[P, R2]:
        return Event(kind=self.kind, payload=self.payload, meta=meta)
```

Why this shape and not the others:

1. **It is the only one all four checkers accept, in 3.12 and 3.13 mode alike** (§1.2). The
   snippet above was re-run verbatim (`variant_final.py`, with `ReplyChannel(Protocol[R])` sharing
   the declared `R`): T1–T6 give exactly the expected diagnostics in all eight runs, and
   `assert_type(e_slot.derive(meta=m_never), Event[InteractiveAction, Never])` passes as well.
   Variants A and B fail three of four; C fails ty's consistency check; D and E pass by giving up
   the property the design wants.
2. **Inference is not available to us, so the declaration is not a workaround but the spelling.**
   The floor forbids the `R = Never` default in PEP 695 syntax; the old-style `TypeVar` the compat
   module provides cannot carry `infer_variance` under mypy (#20313); and even on a 3.13 floor the
   synthesised `__replace__` makes inference return invariant in pyright and ty until the upstream
   discussion or PEP 767 resolves it. Declaring variance is also what Trio and AnyIO do for their
   send-shaped capabilities (§3) — the strictly typed libraries do not lean on inference here.
3. **The declaration is truthful.** A frozen dataclass raises on assignment, so `R` really does
   appear only in output positions at runtime; the one synthesised input position, `__replace__`,
   is exactly what ADR-0037's ban already covers — the ban should name `copy.replace` and
   `__replace__` alongside `dataclasses.replace`, since 3.13 made them the same operation.
4. **`R2` on `derive` is the honest signature, not a new power.** An envelope's `R` is nothing but
   the `R` of its `meta`; typing the result by the replacement `EventMeta` states that. ADR-0037
   already says "every field of `EventMeta` is metadata a Middleware is allowed to touch", and
   `reply` is one of those fields. Payload and kind stay untouched (T4b holds in every checker).
   A Middleware that passes `replace(event.meta, seq=…)` gets `Event[P, R]` back unchanged.
5. **Adding a third parameter is one line.** Append `X = TypeVar("X", …, default=…)` after `R`
   (PEP 696 ordering), declare its variance explicitly, write `Event[Posted]` as before. No
   `TypeVarTuple` (always invariant), no keyword generics (Python has none).

What the documents would say:

- **ADR-0036** — replace "Because `R` appears only in an argument position, `Event` is contravariant
  in it" with: `R` is *declared* contravariant on the compat `TypeVar`, because inference is
  unavailable on the 3.12 floor and returns invariant on 3.13 (`__replace__`); cite §1.1 here.
  Strike bullet 3: `ReplyAlreadySent` is Core-owned (§2) — ADR-0035's marker clause governs the
  order of the LLD documents, not the import graph, and a name in a Core return annotation is an
  import. `webhook.md` returns the value; `event.md` defines it beside `ReplyChannel`.
- **ADR-0037** — `derive(*, meta: EventMeta[R2]) -> Event[P, R2]`; extend the banned-spelling
  rule `ST-EVT-01` to `copy.replace(event, …)` and `event.__replace__`.
- **`event.md`** — §3: the signature above, `ReplyAlreadySent` as a Core value in the class
  diagram; §7 *L*: "declared contravariant" with the reason; §9: an explicit exception to
  `ST-TYP-02` for `Event`, `EventMeta` and `ReplyChannel` (old-style `TypeVar` from the compat
  module) that is not marked temporary; §10: the typing tests T1–T6 of §1.2, run under all four
  checkers in both `3.12` and `3.13` mode, plus `assert_type(e.derive(meta=m_never), Event[P, Never])`
  and a watch on pyrefly's spurious `bad-return`.
- **ADR-0032 / import-linter** — nothing changes; the move of the marker is what keeps the Core
  `forbidden` contract green.

## Sources

Typing standards

- Typing spec, *Generics* — variance definitions, variance inference algorithm, defaults for type
  parameters, bare generics as `Any`: <https://typing.python.org/en/latest/spec/generics.html>
- Typing spec, *Special types*, `Never`: <https://typing.python.org/en/latest/spec/special-types.html#never>
- PEP 695 — type parameter syntax, `infer_variance`: <https://peps.python.org/pep-0695/>
- PEP 696 — type defaults for type parameters (3.13): <https://peps.python.org/pep-0696/>
- PEP 661 — sentinel values (Final, 3.15): <https://peps.python.org/pep-0661/>
- PEP 767 — annotating read-only attributes (Draft, 3.15): <https://peps.python.org/pep-0767/>

Checker behaviour

- discuss.python.org, *Make `__replace__` stop interfering with variance inference* (2025-06 →
  2025-08): <https://discuss.python.org/t/make-replace-stop-interfering-with-variance-inference/96092>
- pyright discussion #11012, frozen dataclass variance in 3.13 mode:
  <https://github.com/microsoft/pyright/discussions/11012>; issue #9241:
  <https://github.com/microsoft/pyright/issues/9241>; issue #8565:
  <https://github.com/microsoft/pyright/issues/8565>
- mypy issue #20313, `infer_variance` rejected on `TypeVar()`: <https://github.com/python/mypy/issues/20313>
- mypy docs, *Generics* — variance, automatic inference with PEP 695 syntax:
  <https://mypy.readthedocs.io/en/stable/generics.html>
- pyrefly docs, *Typing for Python developers* — variance inference:
  <https://pyrefly.org/en/docs/typing-for-python-developers/>
- ty rule reference, `invalid-generic-class`: <https://docs.astral.sh/ty/reference/rules/>
- Empirical runs: mypy 2.3.1, pyright 1.1.411, pyrefly 1.2.0, ty 0.0.79, typing_extensions 4.16.0,
  2026-09-08; snippets `common.py`, `variant_{a,b,b312,c,c2,d,e,f}.py`, `probe{_meta,2,3,4}.py`
  (scratch, not committed).

Libraries (default branches, read 2026-09-08)

- Litestar `litestar/connection/base.py`, `litestar/connection/request.py`:
  <https://github.com/litestar-org/litestar/tree/main/litestar/connection>; guards documentation:
  <https://docs.litestar.dev/latest/usage/security/guards.html>
- Starlette `starlette/requests.py`: <https://github.com/Kludex/starlette/blob/main/starlette/requests.py>
- Trio `src/trio/_abc.py`, `src/trio/_channel.py`: <https://github.com/python-trio/trio/tree/main/src/trio>
- AnyIO `src/anyio/abc/_streams.py`, `src/anyio/streams/memory.py`:
  <https://github.com/agronholm/anyio/tree/master/src/anyio>
- django-modern-rest `dmr/components.py`, `dmr/controller.py`, `.importlinter`:
  <https://github.com/wemake-services/django-modern-rest>
- refactoring.guru, design-pattern catalogue: <https://refactoring.guru/design-patterns/catalog>
