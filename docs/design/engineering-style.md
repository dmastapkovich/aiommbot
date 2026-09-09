# Engineering style and ideology

_Status: reviewed (#36)._

The rules every component design document and, later, every pull request obeys. This document
answers one question: **what does code in this repository have to look like, and what enforces
it?** Decisions live in their ADRs and are linked, never restated; this is where a decision becomes
a rule somebody can apply to a diff.

## How to read a rule

Every rule carries the eight parts [ADR-0033](../adr/0033-identified-tiered-rules-with-a-derived-review-checklist.md)
fixed. There are 94 rules over ten areas, 44 of them `tool` and 50 `review`; the numbers are
derived from the rules below, and a rule added or withdrawn changes them here in the same commit.

| Part | What it is |
|---|---|
| `ST-<AREA>-NN` | The identifier. Stable forever: never renumbered, never reused; a withdrawn rule keeps its number and says so. Cite it — from a component document, from a review comment, from a semgrep rule name. |
| The rule | One imperative sentence, stated positively: *do X*. |
| _Reason_ | One line. Why the rule exists, not what it says. |
| Example | At least one do/don't pair. A rule without an example is unfinished. |
| _Limits_ | When the rule does not apply — or the words **no exceptions**. |
| _Tier_ | `tool` — a linter, a checker, a contract or a test already rejects the violation, and the rule exists to explain it. `review` — nothing mechanical can decide it. |
| _Checked in_ | `LLD` — asked of a component design document, because the document states the property. `PR` — asked of a diff, because the diff shows it. Most rules are both. |
| _From_ | The ADR or research note the rule descends from; for naming and documentation rules, the upstream standard ([`documentation-style.md`](../documentation-style.md), [`CONTEXT.md`](../../CONTEXT.md)); where no decision record exists yet, the words *this document (#N)*. |

The tool configuration is not here. Which ruff rules, which WPS limits, which semgrep rules and
which import-linter contracts run is [ADR-0011](../adr/0011-lint-format-and-architecture-toolchain.md)'s
single responsibility; this document names the tier and, where a semgrep rule carries the same
identifier as the rule it enforces, that identifier. Where this document meets a neighbour, the
**rule** is this document's line and the **realisation** is the neighbour's: package paths, `__all__`
and extras are #24's, the testing toolkit's shape is #25's, the documentation stack is #26's, the
observability boundary and the observer record are #29's.

## 1. Ideology

Nine statements. They are not rules — a creed cannot be checked against a diff — so they carry no
identifier. Each one ends with the rules that hold it up, which is the only way it reaches a review.

**The Core earns its scope; it does not accumulate it.** A capability enters the Core only if every
bot needs it identically, or if it is specific to a chat protocol and has no mature library
equivalent. Everything else is a Plugin, an extra, or a documented recipe. A capability shipped in the Core
can never be removed quietly, so a Core that grows by convenience ends up carrying scheduling,
metrics, retries, a breaker and a CLI that most bots never call and every bot must load.
_Held by:_ `ST-MOD-07`, `ST-MOD-08`, `ST-PAT-04`. _From:_ [ADR-0002](../adr/0002-core-scope-two-condition-test.md).

**Things are composed, not inherited.** The Bot *has* routers, plugins, a Transport and an Adapter;
it is not a Router. No class in this framework is designed to be subclassed by the people who use
it, and the two places inheritance remains the right tool — the error taxonomy (`ST-ERR-09`) and
closed variant types (`ST-PAT-10`) — are named rather than assumed.
_Held by:_ `ST-PAT-05`, `ST-PAT-07`, `ST-PAT-08`, `ST-PAT-10`, `ST-TYP-08`, `ST-SOL-02`. _From:_ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md).

**The Core owns the Protocols; implementations arrive from outside.** Fourteen Protocols on twelve
seams are the whole substitution surface: eleven seams the Core calls out through, and one it hands
to a Handler to call. Imports point at the Core: testing toolkit → adapter-specific plugins →
(Adapter · generic plugins) → Core. A generic Plugin may not import the Adapter, which is
what makes "generic" a checked property instead of a claim.
_Held by:_ `ST-SOL-04`, `ST-SOL-05`, `ST-MOD-05`, `ST-MOD-10`. _From:_ [ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md), [ADR-0038](../adr/0038-seam-inventory-records-the-direction-of-the-call.md).

**A pattern is named and argued, or it is not a pattern.** Every applied pattern is named as on
[refactoring.guru](https://refactoring.guru/design-patterns), with the problem it solves *here* and
the alternative that lost. A catalogue entry is argued once so a component document can cite it;
anything outside the catalogue is argued in that document.
_Held by:_ `ST-PAT-01`, `ST-PAT-02`, `ST-PAT-03`. _From:_ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md).

**Nothing is global.** No module-level mutable state, no singleton, no `get_current()`, no ambient
context. One Bot per process is the documented model and several must still work side by side in
one test session — which is also what keeps the package honest on the free-threaded build.
_Held by:_ `ST-PAT-06`, `ST-MOD-07`, `ST-TYP-16`. _From:_ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md), [ADR-0008](../adr/0008-python-floor-3-12-with-typing-extensions.md).

**Inbound events are immutable and outcomes are typed.** An Event is frozen, constructors are
keyword-only, and a component that has something to say says it in a named type — never in a
dictionary, a tuple or a bare boolean.
_Held by:_ `ST-TYP-05`, `ST-TYP-12`, `ST-ERR-01`, `ST-ERR-04`. _From:_ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md), [ADR-0034](../adr/0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md).

**Handlers are declarative and thin.** Filtering, state gating, payload parsing and dependency
injection all happen outside the handler body; the body makes one service call and answers.
Handlers, filters and events are introspectable as data, so a handler catalogue can be generated
from them rather than maintained beside them.
_Held by:_ `ST-SOL-01`, `ST-TYP-12`, `ST-ERR-07`. _From:_ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md), [ADR-0013](../adr/0013-type-driven-routing-with-a-typed-dispatch-outcome.md).

**Typing is the contract, and four checkers keep it honest.** Python 3.12 features are the
baseline, the package carries no suppression outside two named places, and what the type system
cannot express is a design problem to solve rather than a comment to write.
_Held by:_ the whole of §4, and `ST-TYP-14` in particular. _From:_ [ADR-0009](../adr/0009-four-strict-type-checkers.md), [ADR-0010](../adr/0010-zero-suppressions-with-a-quarantine.md).

**Everything fails closed.** An unknown handler parameter, a missing plugin dependency, an
in-memory backend without a single-process declaration, a Flag no middleware consumes, a
contradicted import contract — each stops start-up with the full list of what is wrong, rather than
degrading quietly at the first event.
_Held by:_ `ST-ERR-06`, `ST-ERR-07`, `ST-ASY-08`. _From:_ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md), [ADR-0016](../adr/0016-three-phase-start-with-checks.md).

## 2. SOLID, as it applies here — `ST-SOL`

One rule per principle. A component design document argues each of them for its own component; the
statement it argues against is the one below.

#### `ST-SOL-01` — Give a module one reason to change, and name that reason in its document

_Reason:_ a class with several reasons to change is edited by several people for unrelated motives,
which is how a `Bot` that is also a `Router` comes to own connecting, scheduling and measuring
as well.

```python
# Don't — one class routing, connecting, scheduling and measuring
class Bot(Router):
    def include_router(self, r): ...
    async def connect_websocket(self): ...
    def schedule(self, cron): ...
    def metrics(self): ...

# Do — the Bot composes; each concern is a component with its own document
class Bot:
    __slots__ = ('_adapter', '_plugins', '_router', '_dispatcher')
```

_Limits:_ a component may still hold *parts* ([§5.10 of the building-block view](05-building-block-view.md#510-inventory-summary)) — a part is not a
second reason to change, it is a named piece of the same one.
_Tier:_ `review`, with WPS as the mechanical floor.
_Checked in:_ LLD, PR. _From:_ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md).

#### `ST-SOL-02` — Extend the framework by adding a Plugin or an implementation of a Protocol, never by editing the component that dispatches

_Reason:_ a new capability that requires a branch in the Core makes every future capability require
one too.

```python
# Don't — the Dispatcher learns about a payload
if isinstance(event.payload, ReactionAdded):
    ...

# Do — the payload is registered, the Dispatcher stays ignorant of it
registry.register('reaction_added', ReactionAdded)
```

_Limits:_ adding a **seam** to the Core is a real design change and belongs in an ADR — this rule
forbids the branch, not the seam.
_Tier:_ `review`. _Checked in:_ LLD, PR. _From:_ [ADR-0012](../adr/0012-generic-event-envelope-with-adapter-payloads.md), [ADR-0015](../adr/0015-plugin-contract-and-composition.md).

#### `ST-SOL-03` — Make every implementation of a Protocol pass that Protocol's conformance suite unchanged

_Reason:_ substitutability that is promised in prose and not executed is discovered by the first
person who swaps the implementation in production.

```python
# Don't — a backend that quietly drops a capability it declares
async def set(self, key, value, *, ttl=None):
    await self._redis.set(key, value)          # ttl ignored

# Do — either honour it, or declare the capability absent so the Check fails at start-up
async def set(self, key, value, *, ttl=None):
    await self._redis.set(key, value, px=_ms(ttl) if ttl else None)
```

_Limits:_ a Protocol may declare an **optional** capability (`KeyValueStore`'s TTL); declining it
explicitly is substitutable, silently ignoring it is not.
_Tier:_ `tool` — the conformance suites of `aiommbot.testing`. _Checked in:_ LLD, PR.
_From:_ [ADR-0022](../adr/0022-state-plugin-model.md).

#### `ST-SOL-04` — Size a Protocol to one consumer's need, and split it when two consumers need different halves

_Reason:_ a wide Protocol forces every implementer to write methods nobody calls, which is how a
"storage profile" ends up binding state, locks and idempotency to one backend.

```python
# Don't — one Protocol for three unrelated capabilities
class Storage(Protocol):
    async def get(...): ...
    async def lock(...): ...
    async def seen(...): ...

# Do — two Protocols, chosen independently
class KeyValueStore(Protocol): ...
class LockProvider(Protocol): ...
```

_Limits:_ no exceptions. Two Protocols implemented by the same class is normal and costs nothing.
_Tier:_ `review`. _Checked in:_ LLD. _From:_ [ADR-0022](../adr/0022-state-plugin-model.md), [`docs/research/07`](../research/07-durable-bot-state-storage.md).

#### `ST-SOL-05` — Depend on a Core-owned Protocol, in the direction the layer table allows

_Reason:_ a dependency that runs the wrong way turns "a second adapter is an addition" into "a
second adapter is a rewrite".

```python
# Don't — a generic Plugin reaching for platform vocabulary
from aiommbot.mattermost import Post          # State is a generic Plugin

# Do — consume the Core seam and receive the Adapter's implementation by injection
from aiommbot import StateKeyProvider
```

_Limits:_ no exceptions. Where an adapter-specific plugin is consulted *by* the Adapter, the
Protocol is Adapter-owned and the import still runs upward.
_Tier:_ `tool` — import-linter. _Checked in:_ LLD, PR. _From:_ [ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md).

## 3. Pattern catalogue — `ST-PAT`

Three tiers. **Welcome** patterns are argued here once, so a component document cites the entry and
names its place. **Restricted** patterns need an ADR that names the rejected alternative. **Banned**
patterns have no exception.

### 3.1 Welcome

Two rows are named outside the design-pattern catalogue refactoring.guru keeps: **Registry** has
no page there, and **Null Object** is documented as a refactoring rather than a pattern. Both are
listed so a component document has one stable name to cite for a shape it will meet anyway.

| Pattern | Where it belongs here | What it replaces |
|---|---|---|
| [Strategy](https://refactoring.guru/design-patterns/strategy) | Filter, `OverflowPolicy`, `RetryPolicy`, the StateKey strategy | a flag parameter and a branch |
| [Chain of Responsibility](https://refactoring.guru/design-patterns/chain-of-responsibility) | the Inbound and Handler middleware layers | a list of callables called in a fixed place |
| [Composite](https://refactoring.guru/design-patterns/composite) | the Router tree | a flat table of routes with priorities |
| [Observer](https://refactoring.guru/design-patterns/observer) | `Signal[T]` lifecycle notifications | callbacks passed into constructors |
| [Adapter](https://refactoring.guru/design-patterns/adapter) | the Mattermost Adapter; every Quarantine module | conditional imports at call sites |
| [Facade](https://refactoring.guru/design-patterns/facade) | the public root namespace; Runtime over Workspace and the API client | asking a Handler to assemble three objects |
| [Mediator](https://refactoring.guru/design-patterns/mediator) | the Dispatcher | components calling each other directly |
| [Builder](https://refactoring.guru/design-patterns/builder) | attachment, button, select and dialog composition | hand-built payload dictionaries |
| [State](https://refactoring.guru/design-patterns/state) | `Flow[Data]` and `StateContext` | a status string compared with `==` |
| [Command](https://refactoring.guru/design-patterns/command) | the frozen `Operation` descriptors | a method per endpoint with a hand-written request |
| [Decorator](https://refactoring.guru/design-patterns/decorator) | observing or changing HTTP behaviour by wrapping `HTTPTransport` | an observer that is allowed to mutate the call |
| [Bridge](https://refactoring.guru/design-patterns/bridge) | the two Faces over one Exchange | a second hand-written client, or generating one from the other |
| Registry (a declarative map, resolved at composition) | `EventRegistry`, the Provider set, the Check set | discovery by import side effect |
| [Introduce Null Object](https://refactoring.guru/introduce-null-object) (a refactoring, not a GoF pattern) | the no-op observer default, disabled event isolation | `if observer is not None` at every call site |

#### `ST-PAT-01` — Name every applied pattern as on refactoring.guru, with the problem it solves here and the alternative you rejected

_Reason:_ a pattern named without its problem is decoration; the rejected alternative is the part a
future reader cannot reconstruct.

```markdown
<!-- Don't -->
We use a Strategy here.

<!-- Do -->
**Strategy** — the per-kind overflow decision varies independently of the queue that applies it.
Rejected: a boolean `drop_oldest` on the queue, which cannot express "drop this kind, block on
that one" (ADR-0023).
```

_Limits:_ a pattern from the table above is cited, not re-argued — see `ST-PAT-02`.
_Tier:_ `review`. _Checked in:_ LLD. _From:_ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md).

#### `ST-PAT-02` — Cite a welcome pattern's catalogue row and name your place in it

_Reason:_ the argument is already made here, so repeating it in 27 documents only creates 27 chances
to make it differently.

```markdown
<!-- Don't — re-arguing Chain of Responsibility from first principles -->
<!-- Do -->
**Chain of Responsibility** (§3.1) — this component is the Handler layer of that chain.
```

_Limits:_ if your use differs from the row's stated place, it is not the catalogue's case and
`ST-PAT-01` applies in full.
_Tier:_ `review`. _Checked in:_ LLD. _From:_ [ADR-0033](../adr/0033-identified-tiered-rules-with-a-derived-review-checklist.md).

### 3.2 Restricted — an ADR naming the rejected alternative

| Pattern | Why it is restricted rather than banned |
|---|---|
| [Template Method](https://refactoring.guru/design-patterns/template-method) | inside one component it can be the honest shape of a fixed algorithm with one varying step; it never becomes a user-facing extension point, which §3.3 bans by that name |
| `abc.ABC` for a family of implementations | a genuinely shared implementation inside one component is cheaper than a Protocol plus duplication — but it re-introduces the coupling ADR-0032 removes, so it needs an argument |
| [Abstract Factory](https://refactoring.guru/design-patterns/abstract-factory) | one factory per family is usually a `Provider` (ADR-0018) wearing a costume |
| [Memento](https://refactoring.guru/design-patterns/memento) | Flow data is versioned and stored, not snapshotted in memory — a history feature would need one, and would need to argue its bound |
| [Proxy](https://refactoring.guru/design-patterns/proxy) | indistinguishable from Decorator at a glance, and the distinction matters for who creates and closes the wrapped object |

#### `ST-PAT-03` — Support a restricted pattern with an ADR that names the alternative it beat

_Reason:_ these are the patterns that look right locally and cost something globally, so the
argument has to survive the session that made it.

```markdown
<!-- Don't -->
`_BaseThrottle` is an ABC because both faces share the arithmetic.

<!-- Do -->
See ADR-0040 (for example): an ABC inside this component, rejected alternative a Protocol plus a shared
sans-I/O function, which loses the invariant that both faces validate identically.
```

_Limits:_ none of these may cross a component boundary, whatever the ADR says.
_Tier:_ `review`. _Checked in:_ LLD. _From:_ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md).

### 3.3 Banned — no exception

| Banned | Reason | What enforces it |
|---|---|---|
| Singleton, module-level mutable state, `get_current()` | several Bots must coexist in one test session, and mutable module state is what breaks a pure-Python package on the free-threaded build | `semgrep:ST-PAT-06`, WPS |
| Service Locator | it hides the dependency graph the check phase exists to validate, moving a start-up failure to the first event | `semgrep:ST-PAT-06`, `review` |
| God object | one class that routes, connects, schedules and measures cannot be read, tested or replaced in parts | WPS |
| Deep inheritance and mixin soup | more than one level of framework class outside the error taxonomy ([ADR-0027](../adr/0027-api-error-taxonomy.md)) and closed variant types (`ST-PAT-10`) means the behaviour of a leaf cannot be read in one place | `review`, `ST-PAT-08`, `ST-PAT-10` |
| Any user-facing extension point by subclassing | it makes every internal refactor a breaking change for users | `ST-TYP-08` (`@final`), `review` |
| Name-based dependency injection | it fails open: a mistyped parameter silently receives `None` and the handler runs anyway | `ST-TYP-12`, `ST-ERR-06` |
| A magic filter DSL | an injected value keyed by a runtime string is invisible to four checkers | `ST-TYP-12`, `review` |
| Dictionary-as-record: a `data` bag, `**kwargs` payloads, tuple returns | a bag has no contract, so nobody can tell what a middleware is allowed to put in it | `semgrep:ST-TYP-12` for the `**kwargs` half, WPS for the `data` name, `ST-ERR-01` for the tuple return |
| Active Record | it binds a wire model to a storage backend the Core is not allowed to know about | import-linter `forbidden` |
| Ambient context for the Bot or the Event | it removes the argument that makes a Handler testable in isolation | `ST-PAT-06`, `ST-TYP-16` |
| `dataclasses.replace`, `copy.replace` or `__replace__` on an `Event` | it can swap the payload under a `kind` that still names the old one, and the next link trusts what it receives | `semgrep:ST-TYP-17` |
| Registration by import side effect | functionality active because a module was imported is functionality nobody chose | `ST-MOD-07` |
| Exceptions as ordinary control flow across a seam | a participant that raises "not me" makes the walk uninterruptible for real failures | `ST-ERR-03` |
| Monkeypatching our own classes in tests | it proves a method was called, not that the method does what it promises | `ST-TST-01` |

#### `ST-PAT-04` — Keep a capability out of the Core unless every bot needs it identically or it is chat-specific with no library equivalent

_Reason:_ a Plugin can be added when a bot needs it; a shipped Core capability can never be removed
quietly.

```python
# Don't — the Core grows a scheduler because one bot wanted one
class Bot:
    def schedule(self, cron: str): ...

# Do — the Core offers the seam; the capability is composed in
Bot(adapter=..., plugins=[SchedulerPlugin(...)])
```

_Limits:_ the two admitted classes are listed in ADR-0002; a candidate that fits neither is a
Plugin, an extra or a recipe.
_Tier:_ `review`. _Checked in:_ LLD. _From:_ [ADR-0002](../adr/0002-core-scope-two-condition-test.md), [`docs/research/08`](../research/08-peer-responsibility-boundaries.md).

#### `ST-PAT-05` — Compose collaborators through the constructor

_Reason:_ composition is what lets a test replace one collaborator; a subclass replaces the whole
class and pins every internal name it touches.

```python
# Don't — replacing a collaborator by overriding the class that uses it
class MyBot(Bot):
    async def dispatch(self, event): ...

# Do — every collaborator arrives as an argument
bot = Bot(adapter=MattermostAdapter(...), plugins=[State(store=InMemoryKeyValueStore())])
```

_Limits:_ a collaborator with exactly one sensible implementation may be built inside the
constructor when the document says so. Whether the class is `@final` is `ST-TYP-08`'s question.
_Tier:_ `review`. _Checked in:_ LLD, PR.
_From:_ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md).

#### `ST-PAT-06` — Pass state through arguments and hold it in an instance the caller owns

_Reason:_ module-level state makes two Bots in one process share what they must not, and makes the
package unsafe on the free-threaded build the CI matrix blocks on.

```python
# Don't
_CURRENT_BOT: Bot | None = None
def get_current() -> Bot: ...

# Do
class Dispatcher:
    __slots__ = ('_router', '_middleware')
    def __init__(self, *, router: Router, middleware: MiddlewareChain) -> None: ...
```

_Limits:_ an immutable module-level `Final` constant is not state. A process-wide cache is state and
belongs to a component that documents its invariants.
_Tier:_ `tool` — `semgrep:ST-PAT-06`, WPS. _Checked in:_ LLD, PR.
_From:_ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md), [`docs/research/04`](../research/04-modern-python-library-engineering-2026.md).

#### `ST-PAT-07` — Express a seam as a Protocol the Core owns, and confine `abc.ABC` to one component's own implementation family

_Reason:_ a Protocol needs no import from the implementer, which is exactly the coupling the layer
table removes; an ABC across a component boundary puts it back.

```python
# Don't — an abstract base every backend must import from the Core
class BaseStore(abc.ABC):
    @abc.abstractmethod
    async def get(self, key: str) -> bytes | None: ...

# Do — a Protocol; the Redis backend never imports it to satisfy it
class KeyValueStore(Protocol):
    async def get(self, key: str) -> bytes | None: ...
```

_Limits:_ an ABC inside a single component, for a family of interchangeable implementations of that
component's own concept, is `restricted` — permitted with the ADR `ST-PAT-03` requires. It never
crosses a component boundary and is never a user extension point.
_Tier:_ `review`, with the import-linter contracts as the boundary floor. _Checked in:_ LLD, PR.
_From:_ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md), [ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md).

#### `ST-PAT-08` — Share behaviour between an asynchronous and a synchronous pair through a private `_Base…` class inside the component, and share it no other way

_Reason:_ the one place duplication is structurally forced is the two faces, and a named private
base is cheaper to read than two copies kept in step by comments.

```python
# Don't — a public mixin anybody can inherit, or twin copies kept in step by a NOTE
class ValidationMixin: ...
# NOTE: if you change this, also change it in the sync version

# Do
class _BaseExchange:
    __slots__ = ()
    def classify(self, status: int) -> Attempt: ...
```

_Limits:_ only for an async/sync pair, only private, only inside one component. Any other shared
behaviour is a function, a component, or a Core Protocol.
_Tier:_ `review`. _Checked in:_ LLD, PR. _From:_ [ADR-0029](../adr/0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md), [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md).

#### `ST-PAT-09` — List the patterns you considered and did not use, with the reason

_Reason:_ the absent pattern is the question every reviewer asks first, and answering it once is
cheaper than answering it in review.

```markdown
<!-- Don't -->
No other patterns apply.

<!-- Do -->
Considered and unused: **Memento** — Flow data is versioned in storage, so an in-memory snapshot
would be a second source of truth (ADR-0022). **Visitor** — payload handling is dispatched by
annotation, so there is no traversal to double-dispatch.
```

_Limits:_ only patterns a reader would plausibly expect here; the list is an argument, not an
inventory of the catalogue.
_Tier:_ `review`. _Checked in:_ LLD. _From:_ this document (#36); no ADR.

#### `ST-PAT-10` — Model a closed set of alternatives as a base with frozen dataclass members

_Reason:_ a closed set spelled as one base and a listed set of frozen, `@final` members lets a
`match` be exhaustive and lets each member carry its own fields, where a tag-and-bag hides the
fields and an open hierarchy invites the member nobody designed.

```python
# Don't — an open hierarchy anyone may extend, or a tag plus a bag
class Outcome: ...
outcome = {'status': 'failed', 'error': exc}

# Do — the base names the set and carries nothing; each member is a frozen, final dataclass
class Outcome:
    __slots__ = ()

@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Failed(Outcome):
    error: Exception
```

_Limits:_ the members are listed in the component document and nothing outside that list inherits
from the base. Alternatives without fields are an `Enum`; a union over types that already exist is
a `type` alias, not a base. With the error taxonomy (`ST-ERR-09`), the private `_Base…` of
`ST-PAT-08` and the restricted ABC of `ST-PAT-07`, this is the whole of the inheritance §3 admits.
_Tier:_ `review`. _Checked in:_ LLD, PR. _From:_ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md), [ADR-0034](../adr/0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md).

## 4. Typing — `ST-TYP`

#### `ST-TYP-01` — Declare every constant as `Final[<type>]`

_Reason:_ the annotation states the type the value is allowed to become, which inference cannot
guess: `Final = 30` infers `Literal[30]`, and a constant later widened to `30.5` changes type
silently.

```python
# Don't
PING_INTERVAL = 30
SILENCE_DEADLINE: Final = 60

# Do
#: Application ping interval, in seconds. Mattermost's server ping is 60 s
#: (`docs/research/01`), so we probe at half of it.
PING_INTERVAL: Final[float] = 30.0
```

_Limits:_ no exceptions on module-level constants. A local that never changes is not a constant and
needs no `Final`.
_Tier:_ `review`. _Checked in:_ PR. _From:_ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md) (typing tenet), and `ST-DOC-05` for the citation line.

#### `ST-TYP-02` — Write generics with PEP 695 syntax

_Reason:_ 3.12 is the floor, the syntax scopes the parameter to the thing that declares it, and it
removes the parallel `TypeVar` name that nothing keeps in step with the class.

```python
# Don't
_T = TypeVar('_T')
class Signal(Generic[_T]): ...

# Do
class Signal[T]: ...
type Filter[P] = Callable[[Event[P]], bool]
```

_Limits:_ a parameter needing `default=` comes from the compat module (`ST-TYP-09`), because PEP 696
defaults land in 3.13. `Event`, `EventMeta` and `ReplyChannel` are the one permanent exception: they
declare `R` contravariant on that compat `TypeVar`, because inference is unavailable on the floor
and returns invariant on 3.13
([ADR-0036](../adr/0036-reply-slot-as-a-second-type-parameter-over-a-core-owned-reply-channel.md),
[`docs/research/20`](../research/20-reply-slot-variance-and-capability-typing.md) §1);
`components/event.md` §9 records it.
_Tier:_ `tool` — ruff. _Checked in:_ PR. _From:_ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md), [ADR-0008](../adr/0008-python-floor-3-12-with-typing-extensions.md).

#### `ST-TYP-03` — Type a genuinely open value as `object` and narrow it

_Reason:_ `Any` switches the checkers off for everything downstream of it, so the one place it is
tempting is the one place the contract matters most.

```python
# Don't
def decode(self, raw: Any) -> Any: ...

# Do
def decode[T](self, raw: bytes, into: type[T]) -> T: ...
def note(self, key: str, detail: object) -> None: ...
```

_Limits:_ no exceptions in `aiommbot/`. A Quarantine module may take `Any` from a foreign signature,
and must not let it out.
_Tier:_ `tool` — ruff, `semgrep:ST-TYP-03`. _Checked in:_ LLD, PR. _From:_ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md), [ADR-0011](../adr/0011-lint-format-and-architecture-toolchain.md).

#### `ST-TYP-04` — Narrow with `isinstance`, `TypeIs` or a `Literal` overload instead of asserting a type

_Reason:_ a cast is a claim no checker verifies, so it fails exactly where the assumption was wrong.

```python
# Don't
stored = cast(bytes, await store.get(key))

# Do — `KeyValueStore.get` returns `bytes | None`; the branch is the contract
stored = await store.get(key)
if stored is None:
    return Missing(key=key)
return codec.decode(stored, into=FlowRecord)
```

_Limits:_ no exceptions in `aiommbot/`; Quarantine may cast at the foreign boundary with a rule code
and an upstream link.
_Tier:_ `tool` — ruff. _Checked in:_ LLD, PR. _From:_ [ADR-0010](../adr/0010-zero-suppressions-with-a-quarantine.md), [ADR-0011](../adr/0011-lint-format-and-architecture-toolchain.md).

#### `ST-TYP-05` — Declare anything that crosses a seam as `@dataclass(frozen=True, slots=True, kw_only=True)`

_Reason:_ a value two components share must not be edited by one of them, and keyword-only
construction is what lets a field be added without misbinding an existing call.

```python
# Don't
@dataclass
class EventMeta:
    transport: str
    received_at: datetime

# Do
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class EventMeta:
    transport: str
    received_at: datetime
```

_Limits:_ a component may hold a mutable object internally when its document names the invariant and
the task that owns it — the reconnect loop's connection state, the Sync executor's pool. It may not
hand that object across a seam.
_Tier:_ `tool` — slotscheck, ruff. _Checked in:_ LLD, PR.
_From:_ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md), [ADR-0011](../adr/0011-lint-format-and-architecture-toolchain.md).

#### `ST-TYP-06` — Give every service class `__slots__`

_Reason:_ it makes the attribute set of a long-lived object readable in one line and stops a typo
from silently creating a new field.

```python
# Don't
class Dispatcher:
    def __init__(self, *, router): self.router = router

# Do
class Dispatcher:
    __slots__ = ('_router',)
    def __init__(self, *, router: Router) -> None: self._router = router
```

_Limits:_ Protocols and the ABCs `ST-PAT-07` admits are exempt, listed once in the slotscheck
configuration.
_Tier:_ `tool` — slotscheck. _Checked in:_ PR. _From:_ [ADR-0011](../adr/0011-lint-format-and-architecture-toolchain.md).

#### `ST-TYP-07` — Mark every override with `@override`

_Reason:_ it turns a renamed base method from a silently dead override into a build failure.

```python
# Don't — silently dead the day `_BaseExchange` renames `classify`
class Exchange(_BaseExchange):
    def classify(self, status: int) -> Attempt: ...

# Do
class Exchange(_BaseExchange):
    @override
    def classify(self, status: int) -> Attempt: ...
```

_Limits:_ applies where a nominal base exists — the private `_Base…` of `ST-PAT-08`, a closed
variant base (`ST-PAT-10`), the error taxonomy. A structural implementation of a Protocol carries
no `@override`: there is no base method to check against, and its conformance is the suite's
(`ST-SOL-03`). `override` is a 3.12 name and comes from `typing`, not from the compat module.
_Tier:_ `tool` — the four checkers. _Checked in:_ PR.
_From:_ [ADR-0009](../adr/0009-four-strict-type-checkers.md).

#### `ST-TYP-08` — Mark a class `@final` unless its document names who subclasses it

_Reason:_ the default has to be the safe one, because a class that turns out to be subclassed by
users can never be refactored again.

```python
# Don't
class MattermostClient: ...

# Do
@final
class MattermostClient: ...
```

_Limits:_ the error taxonomy's intermediate classes (`ST-ERR-09`) and the closed variant bases of
`ST-PAT-10` are open by design and say so in their contract section.
_Tier:_ `review`, with four checkers enforcing the consequence. _Checked in:_ LLD, PR.
_From:_ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md).

#### `ST-TYP-09` — Import a typing name newer than the 3.12 floor from the one compat module

_Reason:_ the floor is 3.12 and the contract needs names from 3.13 and later, so exactly one module
decides where each name comes from; anywhere else the import breaks the floor build.

```python
# Don't — the package no longer imports on 3.12
from typing import TypeIs, ReadOnly

# Do
from aiommbot._internal.compat.typing import ReadOnly, TypeIs
```

_Limits:_ names available on 3.12 — `Protocol`, `Final`, `override`, `Self`, `Never`, PEP 695 syntax
— come from `typing` as usual. The compat module is the Quarantine that holds no suppression: it
adapts one library, `typing_extensions`, by re-export alone.
_Tier:_ `tool` — ruff. _Checked in:_ LLD, PR.
_From:_ [ADR-0008](../adr/0008-python-floor-3-12-with-typing-extensions.md).

> Measured ([`docs/research/21`](../research/21-measured-facts-behind-the-rules.md)): with `typing_extensions` imported directly, the same decision is spread
> over 62 import sites and only one name of ten (`TypedDict`) is mechanically protected — nothing
> stops a contributor importing the other nine from `typing` and breaking the floor build. That is
> the failure this rule exists to prevent.

#### `ST-TYP-10` — Read annotations through one helper over `get_type_hints`, and never touch `__annotations__`

_Reason:_ routing and dependency injection both resolve by annotation, and PEP 649 changes what a
raw `__annotations__` read returns on 3.14 — one helper is one place to be right.

```python
# Don't
hints = handler.__annotations__

# Do
hints = resolve_hints(handler)               # wraps get_type_hints; `format` is a parameter
# and an unresolvable annotation is a domain error, never a silent fallback:
raise UnresolvedAnnotationError(handler=handler.__qualname__) from exc
```

_Limits:_ no exceptions. The helper takes the PEP 649 `format` as an argument rather than branching
on the interpreter version.
_Tier:_ `tool` — `semgrep:ST-TYP-10`. _Checked in:_ LLD, PR.
_From:_ [ADR-0008](../adr/0008-python-floor-3-12-with-typing-extensions.md), [ADR-0011](../adr/0011-lint-format-and-architecture-toolchain.md), [`docs/research/04`](../research/04-modern-python-library-engineering-2026.md).

#### `ST-TYP-11` — Import at module scope, so the public contract is readable at runtime

_Reason:_ a name that exists only for the type checker cannot be introspected, and introspection is
how the handler catalogue and the resolution plans are built.

```python
# Don't
if TYPE_CHECKING:
    from aiommbot import Event
def handle(event: 'Event[Posted]') -> None: ...

# Do
from aiommbot import Event
def handle(event: Event[Posted]) -> None: ...
```

_Limits:_ a genuine import cycle is a layering defect to fix per `ST-MOD-05`, not to hide behind a
guard. A deferred import inside a function, for an optional extra, is `ST-MOD-08`'s case.
_Tier:_ `tool` — ruff. _Checked in:_ LLD, PR. _From:_ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md), [ADR-0011](../adr/0011-lint-format-and-architecture-toolchain.md).

#### `ST-TYP-12` — Close every signature the framework calls: annotate each parameter, and accept no `**kwargs`

_Reason:_ an open signature makes injection a runtime match on parameter names, which fails open —
a mistyped name receives `None` and the handler runs anyway.

```python
# Don't
async def handler(event, **kwargs: Any): ...

# Do
async def handler(event: Event[Posted], repo: TicketRepository) -> None: ...
```

_Limits:_ no exceptions on Handlers, Filters, Extractors, Middleware, Providers and Signal
subscribers. An unknown parameter is a Check error, not a warning.
_Tier:_ `tool` — ruff, `semgrep:ST-TYP-12`, the check phase. _Checked in:_ LLD, PR.
_From:_ [ADR-0014](../adr/0014-filters-and-extractors-with-closed-handler-signatures.md), [ADR-0019](../adr/0019-handler-parameter-resolution-rules.md), [`docs/research/03`](../research/03-bot-framework-architectures.md).

#### `ST-TYP-13` — Assert every public generic's inferred type in `tests/typing/`, and assert the negative cases too

_Reason:_ a generic signature that reads correctly can still infer the wrong type, and only an
executed assertion notices.

```python
# Don't — a runtime test of a typing contract; it passes whatever the inferred type is
def test_on_returns_decorator():
    assert callable(router.on(ChatType.DIRECT))

# Do — tests/typing/test_router.py, checked by all four checkers, never run by pytest
assert_type(router.on(ChatType.DIRECT), Callable[[MessageHandler], MessageHandler])

# Do — and the negative case is the point: this must not type-check
router.on(ChatType.DIRECT)(lambda event: None)   # type: ignore[arg-type]
```

_Limits:_ these modules are checked by all four checkers and never imported by pytest, and they are
the one place besides Quarantine where a suppression may appear — see `ST-TYP-14`.
_Tier:_ `tool` — the four checkers, plus every checker's unnecessary-suppression report.
_Checked in:_ LLD, PR. _From:_ [ADR-0009](../adr/0009-four-strict-type-checkers.md), [ADR-0010](../adr/0010-zero-suppressions-with-a-quarantine.md).

#### `ST-TYP-14` — Redesign code a rule rejects, and confine suppressions to Quarantine and `tests/typing/`

_Reason:_ a suppression is a recorded concession, and a project designed before it is written can
start with none.

```python
# Don't — anywhere in aiommbot/
value = client.thing  # type: ignore[attr-defined]

# Do — in _internal/compat/, with a code and an upstream link, counted against a baseline
value = client.thing  # type: ignore[attr-defined]  # upstream: <org>/<repo>#<issue>
```

_Limits:_ two named exceptions and no others. Quarantine's are counted against a baseline that only
decreases; `tests/typing/`'s are not counted, because there the suppression is the assertion.
Tests and documentation examples relax rules by directory in `pyproject.toml`, with reasons, never
inline.
_Tier:_ `tool` — ruff, every checker's unnecessary-suppression report, and the baseline test.
_Checked in:_ LLD, PR. _From:_ [ADR-0010](../adr/0010-zero-suppressions-with-a-quarantine.md).

#### `ST-TYP-15` — Express a parameter that changes the return type as an overload on a `Literal`

_Reason:_ it lets the call site declare which contract it wants and lets the checker hold both sides
to it, instead of returning `T | None` to a caller that knows better.

```python
# Don't
def find(self, key: str, strict: bool = False) -> Handler | None: ...

# Do
@overload
def find(self, key: str, *, strict: Literal[True]) -> Handler: ...
@overload
def find(self, key: str, *, strict: bool = False) -> Handler | None: ...
```

_Limits:_ two overloads at most; a third means the parameter is really a Strategy (§3.1).
_Tier:_ `review`. _Checked in:_ LLD, PR. _From:_ [ADR-0034](../adr/0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md).

#### `ST-TYP-16` — Carry our own state in our own typed value, never as an attribute on a foreign object

_Reason:_ an attribute stashed on somebody else's object is invisible to the type system, so every
read of it costs a suppression — and `aiommbot/` is allowed none.

```python
# Don't
request.__aiommbot_auth__ = principal        # unreadable without type: ignore[attr-defined]

# Do — a derived envelope (ST-TYP-17), or a value published into Event scope per ADR-0020
event = event.derive(meta=replace(event.meta, correlation_id=cid))
```

_Limits:_ none in `aiommbot/`. A Quarantine module adapting a library that requires it says so and
counts the suppression.
_Tier:_ `tool` — `semgrep:ST-TYP-16` and `ST-TYP-14`. _Checked in:_ LLD, PR.
_From:_ [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md), [ADR-0010](../adr/0010-zero-suppressions-with-a-quarantine.md).

> Measured ([`docs/research/21`](../research/21-measured-facts-behind-the-rules.md)): stashing
> framework state on a foreign request object (`request.__dmr_auth__`, `__dmr_endpoint__`, …) is
> the single largest source of `type: ignore` in the peer measured — 16 of its 101, every one of
> them `[attr-defined]`.

#### `ST-TYP-17` — Enrich an Event only through `Event.derive`

_Reason:_ `derive` accepts a replacement `meta` and nothing else, so the payload and the `kind`
can never disagree; `dataclasses.replace` type-checks a swapped payload and hands the next link an
envelope whose `kind` names something it no longer carries.

```python
# Don't — legal for the type checker, and the payload no longer matches `kind`
event = replace(event, payload=normalised)

# Do — `EventMeta` is replaced wholesale; every one of its fields is a Middleware's to touch
event = event.derive(meta=replace(event.meta, correlation_id=cid))
```

_Limits:_ no exceptions. The ban covers `dataclasses.replace`, `copy.replace` and `__replace__` —
one operation under three names on 3.13 — and names `Event` and no other frozen type;
`dataclasses.replace` on an `EventMeta` is the intended spelling.
_Tier:_ `tool` — `semgrep:ST-TYP-17`. _Checked in:_ LLD, PR.
_From:_ [ADR-0037](../adr/0037-derive-is-the-only-enrichment-path-for-an-event.md).

## 5. Async and cancellation — `ST-ASY`

Almost every rule in this section is [ADR-0031](../adr/0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md)
turned into a check somebody can run against a diff.

#### `ST-ASY-01` — Start every task inside a `TaskGroup` owned by a named component

_Reason:_ a task nobody owns is a task nobody cancels, and its exception surfaces as an
"exception was never retrieved" warning long after the context is gone.

```python
# Don't
asyncio.create_task(self._reader())

# Do
async with asyncio.TaskGroup() as tasks:      # owner: WebSocketTransport
    tasks.create_task(self._reader(), name='ws.reader')
    tasks.create_task(self._heartbeat(), name='ws.heartbeat')
```

_Limits:_ no exceptions. The owner is named in the component's document and in the task name.
_Tier:_ `tool` — ruff, `semgrep:ST-ASY-01`. _Checked in:_ LLD, PR.
_From:_ [ADR-0031](../adr/0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md).

#### `ST-ASY-02` — Put every await that touches I/O under an explicit `asyncio.timeout` whose duration is a named setting or `Final` constant

_Reason:_ an await without a deadline is an outage that looks like a hang, and a literal duration is
a deadline nobody can tune or find.

```python
# Don't
reply = await connection.receive()

# Do
async with asyncio.timeout(RECEIVE_DEADLINE):
    reply = await connection.receive()
```

_Limits:_ the timeout may be a parameter of the operation rather than a constant — which is why
`ASYNC109` is an explained ignore (owned by #32). It may not be a literal at the call site.
_Tier:_ `review`, with ruff covering the mechanical cases. _Checked in:_ LLD, PR.
_From:_ [ADR-0031](../adr/0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md), [ADR-0026](../adr/0026-standalone-typed-api-client-over-an-http-transport-protocol.md).

#### `ST-ASY-03` — Put a bounded queue between a producer and its consumer, and never wrap `__anext__` in a timeout

_Reason:_ a cancellation delivered inside `__anext__` finalises the async generator mid-iteration,
which is the hazard PEP 789 describes; a queue makes the deadline belong to the read, not to the
iteration.

```python
# Don't
async with asyncio.timeout(5):
    async for event in transport:
        await handle(event)

# Do
async for event in transport:                 # reader never stalls
    try:
        queue.put_nowait(event)               # bounded
    except asyncio.QueueFull:
        overflow.apply(queue, event)          # the OverflowPolicy for this kind decides
...
async with asyncio.timeout(DISPATCH_DEADLINE):   # one of the Dispatch concurrency coroutines
    event = await queue.get()
```

_Limits:_ no exceptions.
_Tier:_ `review`, with `semgrep:ST-ASY-03` for the literal shape. _Checked in:_ LLD, PR.
_From:_ [ADR-0031](../adr/0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md), [ADR-0023](../adr/0023-websocket-gateway-resilience.md).

#### `ST-ASY-04` — Clean up in `try/finally`, in bounded time, and let `CancelledError` pass

_Reason:_ a caught cancellation turns a graceful stop into a `SIGKILL`, and an unbounded `finally`
does the same thing more slowly.

```python
# Don't
try:
    await self._drain()
except asyncio.CancelledError:
    logger.info('cancelled')

# Do
try:
    await self._drain()
finally:
    async with asyncio.timeout(CLEANUP_DEADLINE):
        await self._close()
```

_Limits:_ no exceptions. `except*` is the way to handle a group, and it re-raises what it does not
own.
_Tier:_ `tool` — ruff, `semgrep:ST-ASY-04`. _Checked in:_ LLD, PR.
_From:_ [ADR-0031](../adr/0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md).

#### `ST-ASY-05` — Use `asyncio.shield` only in the drain

_Reason:_ shielding is how a component keeps working after the process asked it to stop, so exactly
one place in the design is allowed to want that.

```python
# Don't
await asyncio.shield(self._flush_metrics())

# Do — inside the drain of the WebSocketTransport, and nowhere else
await asyncio.shield(self._finish_inflight())
```

_Limits:_ the drain of [ADR-0023](../adr/0023-websocket-gateway-resilience.md), bounded by the
drain deadline that ADR fixes. No other use.
_Tier:_ `tool` — `semgrep:ST-ASY-05`. _Checked in:_ LLD, PR.
_From:_ [ADR-0031](../adr/0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md).

#### `ST-ASY-06` — Lift a solitary exception out of its group with `__cause__` and `__context__` intact, and keep the siblings

_Reason:_ a user calling one operation should see one exception, and a group of three failures must
not become one failure and two silences.

```python
# Don't
except* Exception as group:
    raise group.exceptions[0]

# Do — the helper returns the one exception with `__cause__` and `__context__` untouched,
# and returns the group itself when it has siblings; a bare raise keeps both intact
except* Exception as group:
    raise unwrap_solitary(group)
```

_Limits:_ only at a user-facing boundary; inside a component the group travels as a group.
_Tier:_ `review`. _Checked in:_ LLD, PR. _From:_ [ADR-0031](../adr/0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md).

#### `ST-ASY-07` — Let the application choose the event loop

_Reason:_ an unrelated transitive install must never change how the process runs; `run(loop_factory=…)`
costs the application one documented line and costs us no dependency.

```python
# Don't
try:
    import uvloop; uvloop.install()
except ImportError:
    pass

# Do
bot.run(loop_factory=uvloop.new_event_loop)   # the application's line, in the application
```

_Limits:_ no exceptions. No extra, no auto-installation, no event-loop policy API.
_Tier:_ `review`. _Checked in:_ LLD, PR. _From:_ [ADR-0031](../adr/0031-stdlib-asyncio-with-a-fixed-concurrency-discipline.md).

#### `ST-ASY-08` — Accept a synchronous callable only when `sync_to_thread` is stated, and resolve its colour at registration

_Reason:_ both implicit defaults are footguns — inline blocks the loop, threading taxes a trivial
callable — and deciding at registration is what lets the check phase reject a mismatch before any
event arrives.

```python
# Don't — decide at the first event, by inspecting the callable then
if inspect.iscoroutinefunction(handler): ...

# Do
@router.on(sync_to_thread=True)
def handle(event: Event[Posted]) -> None: ...
```

_Limits:_ Handlers and Providers only. Filters and Extractors may be synchronous and always run
inline; Middleware, Signal subscribers, plugin lifecycle, `RequestObserver` and `Codec` are
coroutine functions — `ST-ASY-10`.
_Tier:_ `tool` — the check phase. _Checked in:_ LLD, PR.
_From:_ [ADR-0030](../adr/0030-synchronous-callables-by-explicit-declaration.md).

#### `ST-ASY-09` — Make a synchronous Handler idempotent, and say so where it is documented

_Reason:_ nobody can stop a running thread, so at the drain deadline the wait is dropped and the
thread is abandoned — the handler may therefore run to completion after the chain around it is gone.

```python
# Don't — a non-idempotent side effect in a threaded handler
@router.on(sync_to_thread=True)
def charge(event: Event[Posted]) -> None:
    billing.charge(event.payload.user_id, 100)

# Do — key the effect so a repeat is a no-op
@router.on(sync_to_thread=True)
def charge(event: Event[Posted]) -> None:
    billing.charge(event.payload.user_id, 100, idempotency_key=event.meta.correlation_id)
```

_Limits:_ applies to `sync_to_thread=True` only; an inline (`False`) callable is on the loop and is
cancelled normally.
_Tier:_ `review`, with the `HandlerAbandoned` Signal making the event observable.
_Checked in:_ LLD, PR. _From:_ [ADR-0030](../adr/0030-synchronous-callables-by-explicit-declaration.md).

#### `ST-ASY-10` — Declare Middleware, Signal subscribers, plugin lifecycle, `RequestObserver`s and `Codec`s as coroutine functions

_Reason:_ these run on the dispatch path with no thread budget of their own, so a synchronous one is
the hazard of blocking the loop without the benefit of a thread.

```python
# Don't
class AuditMiddleware:
    def __call__(self, event, call_next, *deps): ...

# Do
class AuditMiddleware:
    async def __call__(self, event: Event[P], call_next: CallNext[P]) -> Outcome: ...
```

_Limits:_ no exceptions.
_Tier:_ `tool` — the Protocol signatures plus four checkers. _Checked in:_ LLD, PR.
_From:_ [ADR-0030](../adr/0030-synchronous-callables-by-explicit-declaration.md).

#### `ST-ASY-11` — Decide `async def` from the Protocol you implement, not from whether the body awaits

_Reason:_ the colour of a method is part of its contract, so an implementation that happens to need
no await is still async.

```python
# Don't — colour decided by the body; `KeyValueStore.get` is a coroutine function
class InMemoryKeyValueStore:
    def get(self, key: str) -> bytes | None:
        return self._items.get(key)

# Do — no await in the body, and correct
class InMemoryKeyValueStore:
    async def get(self, key: str) -> bytes | None:
        return self._items.get(key)
```

_Limits:_ this is why `RUF029` is an explained ignore; the explanation is owned by #32. It does not
license an `async def` that implements no async contract.
_Tier:_ `review`. _Checked in:_ PR. _From:_ [ADR-0030](../adr/0030-synchronous-callables-by-explicit-declaration.md).

#### `ST-ASY-12` — Send blocking work from inside an asynchronous Handler to `asyncio.to_thread`, not to the Sync executor

_Reason:_ the Sync executor is sized against the WebSocketTransport's Dispatch concurrency, so user
work drawn from the same budget starves dispatch.

```python
# Don't
await bot.sync_executor.submit(render_pdf, doc)

# Do
await asyncio.to_thread(render_pdf, doc)      # the loop's default executor
```

_Limits:_ genuinely CPU-bound work belongs in a process pool the application owns. The Sync executor
is for declared `sync_to_thread` callables only.
_Tier:_ `review`. _Checked in:_ LLD, PR. _From:_ [ADR-0030](../adr/0030-synchronous-callables-by-explicit-declaration.md).

## 6. Errors — `ST-ERR`

#### `ST-ERR-01` — Return a typed outcome when the immediate caller must branch on the result in normal operation

_Reason:_ a refusal the caller is expected to act on is part of the contract, and a union says so
where an exception only interrupts.

```python
# Don't — "not this handler" as an exception
def extract(self, event: Event[Posted]) -> Ticket:
    raise NoMatchError

# Do
def extract(self, event: Event[Posted]) -> Value[Ticket] | NoMatch | Invalid: ...
```

_Limits:_ the outcome must be a closed, domain-named union of frozen types — not a generic
`Result[T, E]`, and not a bare `bool`.
_Tier:_ `review`. _Checked in:_ LLD, PR. _From:_ [ADR-0034](../adr/0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md).

#### `ST-ERR-02` — Raise when a contract is broken or a dependency failed

_Reason:_ between such a failure and the boundary there is no caller with anything useful to decide,
so threading a union through them all only obscures where it is handled.

```python
# Don't
async def create_post(self, ...) -> Post | ApiFailure: ...

# Do
async def create_post(self, ...) -> Post:     # raises ApiError / TransportError
    ...
```

_Limits:_ the exception carries no payload — `ST-ERR-08`.
_Tier:_ `review`. _Checked in:_ LLD, PR. _From:_ [ADR-0027](../adr/0027-api-error-taxonomy.md), [ADR-0034](../adr/0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md).

#### `ST-ERR-03` — Convert "every alternative declined" into an exception at the boundary of the chain, not inside a participant

_Reason:_ a participant that raises to mean "not me" makes the walk uninterruptible for the failures
that are real.

```python
# Don't — a Filter that raises when it does not match
class ChatType:
    def __call__(self, event): raise SkipHandler

# Do — participants decline; the Dispatcher is the boundary that names the outcome
for candidate in self._walk(router, event):
    if (matched := candidate.match(event)) is not None:
        return await self._invoke(matched)
return Unhandled(event=event)
```

_Limits:_ a Handler's `Skip` ([ADR-0013](../adr/0013-type-driven-routing-with-a-typed-dispatch-outcome.md))
is the one named exception, and the Dispatcher converts it by continuing the walk. The boundaries
are named: the Dispatcher for the router walk, the ErrorBoundary for an escaped exception, the
check phase for start-up.
_Tier:_ `review`. _Checked in:_ LLD, PR. _From:_ [ADR-0034](../adr/0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md), [ADR-0013](../adr/0013-type-driven-routing-with-a-typed-dispatch-outcome.md).

#### `ST-ERR-04` — Raise to report the first failure; return a typed outcome to report all of them

_Reason:_ cardinality is what the caller actually needs: a start-up that stops on the first bad
Check makes the operator restart eight times.

```python
# Don't — the first bad Check stops the run; the operator meets the second one next restart
for check in checks:
    if (failure := check(profile)) is not None:
        raise StartupError(failure)

# Do — the check phase returns every failure as a typed outcome; the entry point converts once
def run_checks(checks: Sequence[Check], profile: ProcessProfile) -> CheckReport:
    return CheckReport(
        failures=tuple(f for check in checks if (f := check(profile)) is not None),
    )
```

_Limits:_ no exceptions. This is why the check phase returns every failure and why Signal subscriber
failures are collected rather than swallowed.
_Tier:_ `review`. _Checked in:_ LLD. _From:_ [ADR-0034](../adr/0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md), [ADR-0016](../adr/0016-three-phase-start-with-checks.md), [ADR-0017](../adr/0017-typed-async-lifecycle-signals.md).

#### `ST-ERR-05` — Give each failure exactly one representation

_Reason:_ a failure available both as a union member and as an exception doubles every caller's
handling and guarantees one of the two paths is untested.

```python
# Don't
def verify(self, token: str) -> Verified | Invalid: ...   # and also raises InvalidTokenError

# Do
def verify(self, token: str) -> Verified | Missing | Invalid | Expired | Replayed | ActorMismatch: ...
```

_Limits:_ where both control flows are genuinely wanted, expose the choice to the call site with
`ST-TYP-15` — one implementation, two typed contracts.
_Tier:_ `review`. _Checked in:_ LLD. _From:_ [ADR-0034](../adr/0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md).

#### `ST-ERR-06` — Reject a bad composition at start-up, with the full list of what is wrong

_Reason:_ a misconfiguration that survives start-up is discovered by a user, at the worst possible
moment, with the least possible context.

```python
# Don't — tolerate and hope
if handler_param not in providers:
    logger.warning('unknown parameter %s', handler_param)

# Do
return CheckFailure(
    id='di.unknown-parameter',
    severity=Severity.error,
    message='Handler "greet" declares parameter "repo" and no Provider supplies it.',
    hint='Register a Provider for TicketRepository, or remove the parameter.',
)
```

_Limits:_ no exceptions. An unknown handler parameter, a missing plugin dependency, an in-memory
backend without a single-process declaration, a Flag no Middleware consumes, an unreachable
Handler and a contradicted import contract all stop the start.
_Tier:_ `tool` — the check phase. _Checked in:_ LLD, PR.
_From:_ [ADR-0016](../adr/0016-three-phase-start-with-checks.md), [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md).

#### `ST-ERR-07` — Let an unexpected exception reach the ErrorBoundary, which is the one place it becomes an outcome

_Reason:_ a handler that swallows what it did not expect destroys the only evidence that something
is broken, and the apology it prints instead is all anyone ever sees.

```python
# Don't
try:
    await service.do(event)
except Exception:
    await runtime.answer('Something went wrong')

# Do
await service.do(event)                       # domain outcomes handled explicitly, above
# unexpected exceptions propagate; ErrorBoundary logs without payload and returns Failed(error)
```

_Limits:_ expected domain outcomes are handled explicitly in the handler — that is `ST-ERR-01`, not
an exception to this rule. A user-visible apology is a Middleware's job, above the boundary.
_Tier:_ `review`. _Checked in:_ LLD, PR. _From:_ [ADR-0021](../adr/0021-core-error-boundary.md), [`docs/research/12`](../research/12-error-boundary-conventions.md).

#### `ST-ERR-08` — Carry identifiers, status and classification in an exception, never content

_Reason:_ an exception travels into logs, into Sentry and into a user's terminal, so anything it
holds is effectively published.

```python
# Don't
raise ApiError(status=400, body=response.text, token=token)

# Do
raise BadRequestError(status=400, error_id='api.context_param_not_found',
                      request_id=response.headers.get('X-Request-Id'))
```

_Limits:_ no exceptions. The `AppError` fields [ADR-0027](../adr/0027-api-error-taxonomy.md) names —
`status`, `error_id`, the short server `message`, `request_id` — are allowed; bodies, headers,
tokens, user message text and media are not.
_Tier:_ `review`, with the redaction rules of §9. _Checked in:_ LLD, PR.
_From:_ [ADR-0027](../adr/0027-api-error-taxonomy.md), [ADR-0034](../adr/0034-typed-outcomes-for-caller-branches-exceptions-for-broken-contracts.md).

#### `ST-ERR-09` — Root every error the framework defines at `AiommbotError` and every warning at `AiommbotWarning`

_Reason:_ one root per kind lets an application catch everything the framework raises without
catching everything Python raises, and the `…Error` / `…Warning` suffixes make the taxonomy
readable in a traceback.

```python
# Don't
class UnsolvableAnnotations(Exception): ...

# Do
class AiommbotError(Exception): ...
class UnresolvedAnnotationError(AiommbotError): ...
class AiommbotWarning(UserWarning): ...
```

_Limits:_ `FatalError` deliberately passes the ErrorBoundary; it is still rooted at
`AiommbotError`. Where a built-in states the meaning better (`TypeError`, `ValueError` for
programmer input), use the built-in.
_Tier:_ `tool` — ruff. _Checked in:_ LLD, PR.
_From:_ [ADR-0027](../adr/0027-api-error-taxonomy.md), [ADR-0021](../adr/0021-core-error-boundary.md).

> A note on the shape ([`docs/research/21`](../research/21-measured-facts-behind-the-rules.md)): a flat hierarchy with no root class, answering "is this
> user-visible?" by the presence of a `status_code` attribute, forces two hand-maintained tuples
> kept in step by `NOTE: keep this in sync` comments. A root class with the classification as a
> property removes that duty, which is why we take the other option here.

#### `ST-ERR-10` — Expose retryability as a property of the error, not as knowledge the caller reconstructs

_Reason:_ the classification depends on the status, the error id and the transport, so every caller
recomputing it will eventually compute it differently.

```python
# Don't
if isinstance(exc, ApiError) and exc.status in {429, 500, 502, 503, 504}:
    ...

# Do
if exc.retryable:
    ...
```

_Limits:_ none. A `RetryPolicy` may narrow which retryable errors it acts on; it may not redefine
the flag.
_Tier:_ `review`. _Checked in:_ LLD, PR. _From:_ [ADR-0027](../adr/0027-api-error-taxonomy.md).

## 7. Naming — `ST-NAM`

#### `ST-NAM-01` — Name every public thing with its `CONTEXT.md` term, exactly

_Reason:_ the glossary is the only thing keeping the documents, the diagrams, the issues and the
code using one word per concept.

```python
# Don't
class BotEngine: ...        # "engine" is on Core's Avoid list
class ApiManager: ...       # on API client's Avoid list; the term is API client

# Do
class Dispatcher: ...
class MattermostClient: ...
```

_Limits:_ private names inside a component may be shorter, and must still not contradict a term.
_Tier:_ `review`. _Checked in:_ LLD, PR. _From:_ [`documentation-style.md` §5](../documentation-style.md#5-vocabulary), [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md).

#### `ST-NAM-02` — Check a proposed name against every term's `_Avoid_` list, and pick a different word when it collides

_Reason:_ the `_Avoid_` lists are what stop a second word growing for a concept that already has
one — and the collisions are not obvious until you look.

```text
Don't: "driver"   for the two thin I/O layers — on Adapter's Avoid list
Don't: "core"     for the sans-I/O heart     — collides with Core
Don't: "executor" for the Bot's thread pool  — spent on the Operation executor

Do:    Face · Exchange · Sync executor
```

_Limits:_ no exceptions. If no free word fits, the collision is a glossary problem — `ST-NAM-03`.
_Tier:_ `review`. _Checked in:_ LLD, PR. _From:_ [`CONTEXT.md`](../../CONTEXT.md), and the three
collisions #38 resolved this way.

#### `ST-NAM-03` — Add the glossary term in the same commit as the concept that needed it

_Reason:_ a concept named in a document and absent from the glossary is a synonym waiting to be
invented by the next author.

```text
Don't: the document introduces "the loss window" and the glossary never hears about it,
       so the next author writes "the gap", "the hole" and "the missed range".

Do:    one commit — the component document, the CONTEXT.md entry with its own _Avoid_
       list, and the TRACKER row. Resync's entry is what "loss window" now means.
```

_Limits:_ terms are framework concepts, not process vocabulary; `CONTEXT.md` is a glossary and
nothing else.
_Tier:_ `review`. _Checked in:_ LLD. _From:_ [`documentation-style.md` §5](../documentation-style.md#5-vocabulary), [`.agents/domain.md`](../../.agents/domain.md).

#### `ST-NAM-04` — Name a variable after what it holds in this domain

_Reason:_ `data` and `value` describe the language, not the problem, so they make a reader open the
call site to learn what the parameter is.

```python
# Don't
def parse(self, data: bytes, value: str) -> Any: ...

# Do
def parse(self, raw_payload: bytes, event_kind: str) -> Payload: ...
```

_Limits:_ an identifier an external specification forces — an OpenAPI object field, a stdlib
signature — is allowed with a local, justified exemption naming the spec.
_Tier:_ `tool` — WPS. _Checked in:_ PR.
_From:_ [ADR-0011](../adr/0011-lint-format-and-architecture-toolchain.md).

#### `ST-NAM-05` — Give the asynchronous thing the bare name and its synchronous twin the `Sync` prefix

_Reason:_ the asynchronous face is the primary one, so the common case reads without ceremony and
the twin is visibly the exception.

```python
# Don't
class AsyncMattermostClient: ...
class MattermostClient: ...        # which one is the default?

# Do
class MattermostClient: ...        # async
class SyncMattermostClient: ...
```

_Limits:_ only four pairs exist by design — the API client, the `Workspace`, `HTTPTransport` and
`TokenProvider`. A fifth pair needs an ADR, because `SyncRuntime` deliberately does not exist.
_Tier:_ `tool` — the typed name-parity test. _Checked in:_ LLD, PR.
_From:_ [ADR-0029](../adr/0029-synchronous-face-from-a-sans-io-core-with-thin-drivers.md), [ADR-0026](../adr/0026-standalone-typed-api-client-over-an-http-transport-protocol.md).

#### `ST-NAM-06` — Name a Protocol for the capability and an implementation for what realises it

_Reason:_ the consumer should read the capability it depends on, and the composition root should read
which thing it plugged in.

```python
# Don't
class IStore(Protocol): ...
class StoreImpl: ...

# Do
class KeyValueStore(Protocol): ...
class InMemoryKeyValueStore: ...
class RedisKeyValueStore: ...
```

_Limits:_ no `I` prefix, no `Impl`/`Base` suffix on a public name. A shipped implementation whose
technology is the point (`MsgspecCodec`) leads with the technology.
_Tier:_ `review`. _Checked in:_ LLD, PR. _From:_ [`CONTEXT.md`](../../CONTEXT.md), [ADR-0006](../adr/0006-architectural-tenets-of-the-core.md).

#### `ST-NAM-07` — Name a module in the plural for a family of interchangeable peers and in the singular for one concept

_Reason:_ the module name should tell a reader whether to expect one thing or a choice of things.

```text
# Don't
filter.py            # ChatType, Command and Regex — a family under a singular name
key_value_stores.py  # one Protocol under a plural name

# Do
dispatcher.py        # one concept
filters.py           # a family of peers
key_value_store.py   # one Protocol
backends/            # a family, each in its own module
```

_Limits:_ a component's module is named after its `CONTEXT.md` term, which wins over this rule when
the two disagree.
_Tier:_ `review`. _Checked in:_ LLD. _From:_ [`documentation-style.md` §4](../documentation-style.md#4-naming).

#### `ST-NAM-08` — Keep a type parameter short, and give it a domain name only when the signature needs one

_Reason:_ `Event[P]` reads as an envelope over a payload; `Event[PayloadTypeVar]` reads as
ceremony — and the existing decisions already fixed the short spellings.

```python
# Don't
class Event[PayloadT_co]: ...

# Do
class Event[P]: ...
class Extractor[P, T]: ...
class Flow[Data]: ...
class Operation[Req, Resp]: ...
```

_Limits:_ two or more parameters whose roles are not obvious from position take domain names, as
`Flow[Data]` and `Operation[Req, Resp]` already do.
_Tier:_ `review`. _Checked in:_ LLD, PR. _From:_ [ADR-0012](../adr/0012-generic-event-envelope-with-adapter-payloads.md), [ADR-0014](../adr/0014-filters-and-extractors-with-closed-handler-signatures.md), [ADR-0022](../adr/0022-state-plugin-model.md), [ADR-0025](../adr/0025-generated-dataclass-models-with-a-codec-protocol.md).

## 8. Module layout and the public surface — `ST-MOD`

This section owns the **rules**. The package paths, the `__all__` policy and the extras that realise
them are #24's; where the two meet, the rule is this section's line and the directory is #24's.

#### `ST-MOD-01` — Treat a name as public only when all four criteria hold

_Reason:_ without a criterion, the public surface becomes whatever happens to import, and the
semantic-versioning promise has nothing to bound it.

```text
Public  ⇔  (1) the name has no leading underscore
       and (2) it lives outside `_internal`
       and (3) its owning subpackage re-exports it explicitly
       and (4) it appears in the reference documentation
```

```python
# Don't — importable, undocumented, and therefore accidentally promised
from aiommbot.dispatch import walk_router

# Do — the four criteria, or it is internal
from aiommbot import Router
```

_Limits:_ no exceptions. A name that fails any criterion may change in a patch release.
_Tier:_ `tool` — the public-surface guard test, plus pyright `--verifytypes`. _Checked in:_ LLD, PR.
_From:_ [ADR-0007](../adr/0007-tiny-public-root-with-explicit-subpackages.md).

#### `ST-MOD-02` — Put everything that is not public under `_internal`

_Reason:_ the boundary has to be visible in an import line, so a reader of somebody else's code can
tell at a glance that it reached into our internals.

```python
# Don't
from aiommbot.resolution import ResolutionPlan

# Do
from aiommbot._internal.di.plan import ResolutionPlan   # and only from inside aiommbot
```

_Limits:_ `aiommbot.testing` is public and may import every layer; nothing may import it.
_Tier:_ `tool` — ruff, import-linter. _Checked in:_ LLD, PR. _From:_ [ADR-0007](../adr/0007-tiny-public-root-with-explicit-subpackages.md), [ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md).

#### `ST-MOD-03` — Re-export a public name explicitly

_Reason:_ an implicit re-export is invisible to a type checker consuming the package, so the name is
public for us and private for our users.

```python
# Don't
from aiommbot.event import Event

# Do
from aiommbot.event import Event as Event
```

_Limits:_ the mechanism — `X as X` or `__all__` — is #24's to fix; this rule requires that it be
explicit either way.
_Tier:_ `tool` — pyright `--verifytypes`, ruff. _Checked in:_ PR.
_From:_ [ADR-0007](../adr/0007-tiny-public-root-with-explicit-subpackages.md), [ADR-0009](../adr/0009-four-strict-type-checkers.md).

#### `ST-MOD-04` — Reach another component only through its public contract

_Reason:_ a component's document promises its contract and nothing else, so an import of its
internals makes that document false.

```python
# Don't
from aiommbot._internal.ws.reader import _ReaderState

# Do
from aiommbot import WebSocketConnection      # the seam the WebSocketTransport is designed around
```

_Limits:_ inside one component, its own `_internal` modules import each other freely.
_Tier:_ `tool` — ruff, import-linter. _Checked in:_ LLD, PR.
_From:_ [ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md).

#### `ST-MOD-05` — Import in the direction the layer table allows

_Reason:_ this is the one architectural property a machine can check, and checking it is what makes
"a second adapter is an addition" true rather than hoped for.

```text
Do: import only downward in this table.

    testing toolkit           → everything below
    adapter-specific plugins  → the Adapter and the Core
    Adapter · generic plugins → the Core only, and never each other
    Core                      → the standard library and the compat module's backport

Don't: State (a generic Plugin) → aiommbot.mattermost
       Webhook → aiommbot.state          (plugins are independent)
       Core → msgspec                    (the Core imports no third-party package)
       Adapter → aiommbot.testing        (nothing imports the toolkit)
```

_Limits:_ no exceptions. A needed import in the wrong direction means a seam is missing — see
`ST-MOD-10`.
_Tier:_ `tool` — import-linter. _Checked in:_ LLD, PR.
_From:_ [ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md).

#### `ST-MOD-06` — Give every contract exception a comment saying why it exists

_Reason:_ an exception without a reason is indistinguishable from a widened rule, and the layer list
is the architecture document — a silent hole in it is a silent hole in the design.

```toml
# Don't
[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]

# Do
[tool.ruff.lint.per-file-ignores]
# Tests assert with the statement. S101 guards against asserts stripped under -O, and test
# code never runs under -O; the relaxation is the one ADR-0010 grants tests by directory.
"tests/**" = ["S101"]
```

_Limits:_ applies to every configured exception — import-linter, per-directory lint relaxations,
slotscheck exclusions, every switched-off checker rule.
_Tier:_ `review`. _Checked in:_ PR. _From:_ [ADR-0009](../adr/0009-four-strict-type-checkers.md), [ADR-0011](../adr/0011-lint-format-and-architecture-toolchain.md), [ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md).

#### `ST-MOD-07` — Make importing any public module free of side effects, extras and configuration

_Reason:_ functionality active because a module was imported is functionality nobody chose, and an
import that needs configuration cannot be type-checked, documented or smoke-tested.

```python
# Don't — at module scope
_REGISTRY[name] = handler
settings = load_settings()

# Do — declare at import, act at composition
@final
@dataclass(frozen=True, slots=True, kw_only=True)
class StateSpec: ...
```

_Limits:_ an immutable module-level `Final` constant, including one read from the environment into a
frozen value, is not a side effect.
_Tier:_ `tool` — the smoke-import recipe: every public module imports with no extras installed.
_Checked in:_ LLD, PR. _From:_ [ADR-0002](../adr/0002-core-scope-two-condition-test.md), [ADR-0015](../adr/0015-plugin-contract-and-composition.md), [`docs/research/10`](../research/10-plugin-systems.md).

#### `ST-MOD-08` — Report a missing extra as a typed error when the object is constructed, not when the module is imported

_Reason:_ an `ImportError` at import time breaks the smoke import of `ST-MOD-07` and tells the user
about a dependency they may not need.

```python
# Don't
import redis                                   # at module scope, in an optional backend

# Do
def __init__(self, *, url: str) -> None:
    try:
        import redis.asyncio as redis
    except ImportError as exc:
        raise MissingExtraError(extra='redis', install='aiommbot[redis]') from exc
```

_Limits:_ the deferred import lives in the constructor of the object that needs it, and nowhere
else; this is the one sanctioned function-local import.
_Tier:_ `review`, with the per-extra smoke imports as the mechanical floor. _Checked in:_ LLD, PR.
_From:_ [ADR-0015](../adr/0015-plugin-contract-and-composition.md), [`docs/research/04`](../research/04-modern-python-library-engineering-2026.md).

#### `ST-MOD-09` — Keep one module to one component or one part

_Reason:_ a module a reader has to navigate by heading has become a package that has not been split
yet.

```text
# Don't
dispatcher.py   # dispatcher + outcomes + matched handler + skip + middleware chain

# Do
dispatcher/__init__.py   outcome.py   matched.py
```

_Limits:_ a part small enough to read in one screen may share its component's module; the component
document's structure section is what decides.
_Tier:_ `tool` — WPS. _Checked in:_ LLD, PR.
_From:_ [ADR-0011](../adr/0011-lint-format-and-architecture-toolchain.md), [`documentation-style.md` §2](../documentation-style.md#2-one-document-one-question).

#### `ST-MOD-10` — Put a capability two plugins need into the Core behind a Protocol, or duplicate it on purpose

_Reason:_ the `independence` contract makes a shared helper between plugins impossible by
construction, and that is deliberate: a shared helper is a seam nobody designed.

```python
# Don't — Webhook's nonce store importing the State plugin's Redis helper
from aiommbot.state.backends.redis import connect

# Do — both reach the Core Protocol the capability implements
def __init__(self, *, store: KeyValueStore) -> None: ...
```

_Limits:_ deliberate duplication is allowed and must say so in both documents; the third occurrence
is a Protocol.
_Tier:_ `tool` — import-linter. _Checked in:_ LLD, PR.
_From:_ [ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md).

## 9. Logging and redaction — `ST-LOG`

These rules cover the whole framework. The observability boundary and the shape of the observer
record are #29's.

#### `ST-LOG-01` — Log through one logger per component, named `aiommbot.<component>`, with a `NullHandler` on the package root

_Reason:_ an application configures logging, a library does not; per-component names are what let it
silence the WebSocketTransport without silencing dispatch.

```python
# Don't
logging.info('connected')                      # the root logger, in a library

# Do
logger = logging.getLogger('aiommbot.websocket_transport')
# and once, in aiommbot/__init__.py:
logging.getLogger('aiommbot').addHandler(logging.NullHandler())
```

_Limits:_ no exceptions. The component name is its `CONTEXT.md` term in snake case.
_Tier:_ `review`. _Checked in:_ LLD, PR. _From:_ [`docs/research/04`](../research/04-modern-python-library-engineering-2026.md), [`docs/research/17`](../research/17-http-client-observability.md).

#### `ST-LOG-02` — Log identifiers, counts and digests; never content

_Reason:_ a log line is copied into tickets, screenshots and third-party log stores, so anything in
it has left the process for good.

```python
# Don't
logger.warning('bad callback: %s', payload)
logger.debug('token=%s', token)

# Do
logger.warning('callback rejected', extra={'reason': 'ActorMismatch',
                                           'post_id': post_id,
                                           'kid': kid})
```

_Limits:_ no exceptions. Identifiers, event kinds, status codes, durations, counts and a truncated
digest of a credential are allowed; message text, media, bodies, headers, query strings, tokens and
personal data are not.
_Tier:_ `review`, with `semgrep:ST-LOG-02` matching the forbidden field names of `ST-LOG-04`.
_Checked in:_ LLD, PR. _From:_ [ADR-0021](../adr/0021-core-error-boundary.md), [ADR-0024](../adr/0024-webhook-ingress-and-callback-security.md), [ADR-0026](../adr/0026-standalone-typed-api-client-over-an-http-transport-protocol.md), [`docs/research/17`](../research/17-http-client-observability.md).

#### `ST-LOG-03` — Ship no switch that turns content logging on

_Reason:_ a switch that prints message text will be enabled in production one day, and the people
in that channel never agreed to it.

```python
# Don't
if settings.log_bodies:
    logger.debug('body=%s', response.text)

# Do — the capability does not exist; an application that needs it decorates HTTPTransport
```

_Limits:_ no exceptions, in any component. An application may add its own observer or transport
decorator — that is its decision, in its code, and `ST-DOC-04` requires our documentation to say so.
_Tier:_ `review`. _Checked in:_ LLD, PR. _From:_ [ADR-0026](../adr/0026-standalone-typed-api-client-over-an-http-transport-protocol.md), [`docs/research/17`](../research/17-http-client-observability.md).

#### `ST-LOG-04` — Keep the forbidden-field list in one named constant that the rules and the tests cite

_Reason:_ a redaction rule repeated in nine components is nine chances to forget a field.

```python
# Don't — each component with its own tuple, kept in step by a comment
_SECRET_KEYS = ('authorization', 'token')     # NOTE: keep in sync with ws/redact.py

# Do
#: Field names that must never reach a log record, an exception or an observer.
REDACTED_FIELDS: Final[frozenset[str]] = frozenset({
    'authorization', 'token', 'password', 'text', 'body', 'props', 'query',
})
```

_Limits:_ the list may only grow. The members shown are illustrative; the exact membership is
#29's to finalise with the observer record, and the rule is that there is exactly one list.
_Tier:_ `tool` — a test asserting no log record and no exception field intersects it.
_Checked in:_ LLD, PR. _From:_ [ADR-0026](../adr/0026-standalone-typed-api-client-over-an-http-transport-protocol.md), [`docs/research/17`](../research/17-http-client-observability.md).

#### `ST-LOG-05` — Write the message as a constant and put the variables in `extra`

_Reason:_ a constant message is what makes a log line groupable, and it is also what keeps untrusted
text out of the message body.

```python
# Don't
logger.info(f'handler {name} matched for {event.payload.message}')

# Do
logger.info('handler matched', extra={'handler': name, 'kind': event.kind})
```

_Limits:_ no exceptions. `structlog` is never a dependency; `extra` on the standard library is the
mechanism.
_Tier:_ `tool` — ruff. _Checked in:_ PR. _From:_ [`docs/research/04`](../research/04-modern-python-library-engineering-2026.md).

#### `ST-LOG-06` — Give a user-visible failure a correlation id and keep the diagnosis in the log

_Reason:_ the user needs something to quote and the operator needs the detail; showing a traceback
serves neither.

```python
# Don't — the Handler catches, apologises with the cause, and the log holds nothing
except Exception as exc:
    await runtime.answer(f'Failed: {exc!r}')

# Do — a Handler-layer Middleware reacts to the Outcome; the ErrorBoundary has already
# written the diagnosis, without payload, under the same correlation id
class ApologyMiddleware:
    __slots__ = ()

    async def __call__(self, event: Event[P], call_next: CallNext[P], runtime: Runtime) -> Outcome:
        outcome = await call_next(event)
        if isinstance(outcome, Failed):
            await runtime.answer(f'Something went wrong. Reference: {event.meta.correlation_id}')
        return outcome
```

_Limits:_ applies to text the framework itself produces; an application's own copy is its business.
_Tier:_ `review`. _Checked in:_ LLD, PR. _From:_ [ADR-0021](../adr/0021-core-error-boundary.md).

## 10. Documentation — `ST-DOC`

The rules are here; the documentation stack that executes them is #26's.

#### `ST-DOC-01` — Give every public name a Google-style docstring

_Reason:_ criterion 4 of `ST-MOD-01` makes documentation the definition of the public surface, so an
undocumented public name is a contradiction rather than an omission.

```python
# Don't — importable and re-exported, and still not public (criterion 4 of ST-MOD-01)
def routes(self) -> tuple[HandlerSpec, ...]: ...

# Do
def routes(self) -> tuple[HandlerSpec, ...]:
    """Return the frozen registration record of every Handler.

    Returns:
        One `HandlerSpec` per registered Handler, in registration order.
    """
```

_Limits:_ `_internal` and tests are exempt, configured once. An `@overload` may carry no docstring;
the implementation must.
_Tier:_ `tool` — ruff. _Checked in:_ LLD, PR.
_From:_ [ADR-0011](../adr/0011-lint-format-and-architecture-toolchain.md), [ADR-0007](../adr/0007-tiny-public-root-with-explicit-subpackages.md).

#### `ST-DOC-02` — Write a docstring example as an executable doctest

_Reason:_ an example that is not executed rots silently, and the first person to notice is a user
following it.

```python
# Don't
"""Example: bot.run(loop_factory=uvloop.new_event_loop)"""

# Do
"""Compose a Bot with one Plugin.

Example:
    >>> bot = Bot(adapter=FakeAdapter(), plugins=[State(store=InMemoryKeyValueStore())])
    >>> [spec.name for spec in bot.plugins()]
    ['state']
"""
```

_Limits:_ an example needing a running server belongs in the documentation's own example tree
(#26), not in a docstring. The code inside a docstring is formatted and linted like any other code.
_Tier:_ `tool` — pytest configuration (doctest collection) and ruff. _Checked in:_ LLD, PR.
_From:_ this document (#36) — executable documentation; the stack that runs it is #26's; no ADR.
Evidence in [`docs/research/21`](../research/21-measured-facts-behind-the-rules.md).

#### `ST-DOC-03` — State a Protocol's contract for its implementer, and name the conformance suite that checks it

_Reason:_ a third-party implementer reads the docstring, not our design catalogue — and a Protocol
without its invariants is an invitation to implement it wrongly.

```python
# Don't — the shape without the promise
class KeyValueStore(Protocol):
    """A key-value store."""

# Do
class KeyValueStore(Protocol):
    """Versioned bytes by key, with compare-and-set.

    Implementers must guarantee:
        * `set` with a stale version returns `Conflict` and writes nothing;
        * `ttl` is honoured or declared unsupported, never silently ignored;
        * keys are opaque bytes-safe strings and are never parsed.

    Conformance:
        `aiommbot.testing.suites.key_value_store`
    """
```

_Limits:_ the suites themselves are #25's to shape; this rule requires the docstring to name the one
that applies.
_Tier:_ `review`, with `ST-SOL-03` making the suite itself blocking. _Checked in:_ LLD, PR.
_From:_ [ADR-0022](../adr/0022-state-plugin-model.md), [ADR-0015](../adr/0015-plugin-contract-and-composition.md).

#### `ST-DOC-04` — Write a comment about why, and cite the source that decided it

_Reason:_ what the code does is readable; why this constant, this order or this workaround is not,
and that is the knowledge a comment can carry and nothing else can.

```python
# Don't
# increment the sequence
seq += 1

# Do
# Mattermost replays at most 128 events from the dead queue, so a gap wider than
# that cannot be resumed and must become a Resync (docs/research/01).
if gap > DEAD_QUEUE_REPLAY:
    raise ResumeImpossible(since=last_seq)
```

_Limits:_ `NOTE:` and `TODO:` are the two admitted prefixes, and a `TODO:` carries an issue number.
A comment that keeps two code paths in step is a design smell, not a citation — see `ST-PAT-08`.
_Tier:_ `review`, with ruff on the mechanical part. _Checked in:_ PR.
_From:_ [`documentation-style.md` §8](../documentation-style.md#8-writing).

#### `ST-DOC-05` — Cite the primary source next to a constant taken from one

_Reason:_ the number is checkable and the reason it is that number is not, so the citation is the
only part a future reader cannot reconstruct.

```python
# Don't
PAGE_SIZE: Final[int] = 200

# Do
#: Mattermost's maximum `per_page`, from the API reference; larger values are clamped by
#: the server (ADR-0026).
PAGE_SIZE: Final[int] = 200
```

_Limits:_ applies to constants derived from a specification, a protocol or measured server
behaviour. A constant we chose ourselves cites the ADR that chose it.
_Tier:_ `review`. _Checked in:_ PR. _From:_ [`documentation-style.md` §8](../documentation-style.md#8-writing), and `ST-TYP-01`.

#### `ST-DOC-06` — Record the release in which a public name appeared or changed

_Reason:_ the reference page is the definition of the public surface, so it has to say since when.

```python
# Don't — since when? the changelog knows, the reference page does not
"""Open a direct channel with a user."""

# Do — the marker the #26 stack defines; shown here in Sphinx form
"""Open a direct channel with a user.

.. versionadded:: 0.5.0
"""
```

_Limits:_ the versioning and deprecation policy is #28's; this rule only requires the marker.
_Tier:_ `review`. _Checked in:_ PR. _From:_ [ADR-0007](../adr/0007-tiny-public-root-with-explicit-subpackages.md).

#### `ST-DOC-07` — Deprecate with `warnings.deprecated` from the compat module, so the type checkers report every use

_Reason:_ a note in a changelog reaches whoever reads changelogs; a decorated symbol reaches
everyone who type-checks.

```python
# Don't
# Deprecated, will be removed in 0.7.0.
def old_helper(...): ...

# Do
@deprecated('Use Workspace.send instead; removed in 0.7.0.')
def old_helper(...) -> None: ...
```

_Limits:_ `warnings.deprecated` is a 3.13 name, so it comes from the compat module (`ST-TYP-09`).
The deprecation window is #28's.
_Tier:_ `tool` — the four checkers. _Checked in:_ PR.
_From:_ [ADR-0008](../adr/0008-python-floor-3-12-with-typing-extensions.md), [`docs/research/04`](../research/04-modern-python-library-engineering-2026.md).

## 11. Tests — `ST-TST`

How tests are written is here; what `aiommbot.testing` provides is #25's.

#### `ST-TST-01` — Double one of our own Protocols with `aiommbot.testing` or with a real implementation of it, and never with a mock or a patched attribute

_Reason:_ a mock proves a method was called; a conforming double proves the method does what the
Protocol promises — and only the second one fails when the promise changes.

```python
# Don't
store = MagicMock(spec=KeyValueStore)
monkeypatch.setattr(dispatcher, '_router', object())

# Do
store = InMemoryKeyValueStore()               # shipped in aiommbot.testing
class _RefusingStore:                         # a real implementation, for one behaviour
    __slots__ = ()
    async def get(self, key: str) -> bytes | None:
        raise DependencyUnavailableError(dependency='store')
```

_Limits:_ `unittest.mock` and `monkeypatch` are allowed against a third-party library or the
standard library, and inside a Quarantine module's tests. Never against our own Protocols, classes
or attributes.
_Tier:_ `tool` — `semgrep:ST-TST-01`. _Checked in:_ LLD, PR.
_From:_ this document (#36); no ADR. Evidence in
[`docs/research/21`](../research/21-measured-facts-behind-the-rules.md): two files in the peer
measured use `unittest.mock`, both at a third-party seam, against forty hand-written conforming
doubles.

#### `ST-TST-02` — Treat an implementation of a Protocol as unfinished until its conformance suite passes

_Reason:_ the suite is the Protocol's contract in executable form, so passing it is what makes
substitutability a fact instead of a claim.

```python
# Don't — a framework class as a subclassing extension point (§3.3)
class TestRedisStore(KeyValueStoreConformance):
    @pytest.fixture
    def store(self) -> KeyValueStore:
        return RedisKeyValueStore(url=REDIS_URL)

# Do — the suite is a parametrised test over a factory the implementer supplies; nothing is subclassed
from aiommbot.testing.suites import key_value_store_conformance

test_redis_store_conforms = key_value_store_conformance(lambda: RedisKeyValueStore(url=REDIS_URL))
```

_Limits:_ a Protocol with exactly one shipped implementation and no extension point may carry unit
tests instead, and its document must say so.
_Tier:_ `tool` — the suites. _Checked in:_ LLD, PR. _From:_ [ADR-0022](../adr/0022-state-plugin-model.md), [ADR-0015](../adr/0015-plugin-contract-and-composition.md).

#### `ST-TST-03` — Test one behaviour per test and name the test after that behaviour

_Reason:_ a failing test name should be the bug report, and a test asserting four things reports the
first of them.

```python
# Don't
def test_dispatcher(): ...

# Do
def test_unmatched_event_returns_unhandled(): ...
def test_handler_exception_becomes_failed_without_payload(): ...
```

_Limits:_ a scenario test walking a workflow is one behaviour — the workflow — and says so in its
name.
_Tier:_ `review`. _Checked in:_ PR. _From:_ this document (#36); no ADR.

#### `ST-TST-04` — Cover every failure mode the component's document lists

_Reason:_ the failure-mode section is a promise about behaviour under failure, and an untested
promise is a guess.

```python
# Don't — the failure-mode table has five rows and the suite has one happy path
def test_receive_and_dispatch(): ...

# Do — one test per row of the document's failure-mode table
def test_receive_timeout_closes_and_reconnects(): ...
def test_cancellation_during_drain_abandons_thread_and_signals(): ...
def test_store_outage_surfaces_as_dependency_error(): ...
def test_duplicate_sequence_is_deduplicated(): ...
```

_Limits:_ timeout, cancellation, dependency outage, bad input and concurrent use are the minimum
set; the document may list more.
_Tier:_ `review`. _Checked in:_ LLD, PR. _From:_ [`design-quality-checklist.md`](../../.agents/design-quality-checklist.md) (the failure-mode line), [ADR-0023](../adr/0023-websocket-gateway-resilience.md).

#### `ST-TST-05` — Reach 100 % coverage by testing the branch, not by excluding it

_Reason:_ an exclusion is a suppression wearing different syntax, and the branches people exclude
are the error branches.

```python
# Don't
except DependencyUnavailableError:            # pragma: no cover
    ...

# Do — a double that fails, and a test that asserts what happens
```

_Limits:_ `# pragma: no cover` is allowed only in Quarantine modules, where the excluded line is an
`except ImportError` for an absent extra. Coverage is measured over the tests as well, so dead test
code fails the build.
_Tier:_ `tool` — pytest configuration (coverage). _Checked in:_ PR.
_From:_ [ADR-0010](../adr/0010-zero-suppressions-with-a-quarantine.md); the coverage bar is this document's (#36), no ADR.

#### `ST-TST-06` — Make a warning fail the suite, and assert the warnings you mean to raise

_Reason:_ `AiommbotWarning` is public API — it is how `sync_to_thread` asks for a decision — so its
text and its trigger are behaviour, not noise.

```python
# Don't — the warning is emitted, nobody asserts it, and the suite stays green when it vanishes
router.on()(sync_handler)

# Do
with pytest.warns(AiommbotWarning, match='sync_to_thread'):
    router.on()(sync_handler)
```

_Limits:_ no exceptions; warnings are configured as errors for the whole suite.
_Tier:_ `tool` — pytest configuration. _Checked in:_ PR.
_From:_ [ADR-0030](../adr/0030-synchronous-callables-by-explicit-declaration.md).

#### `ST-TST-07` — Let a double report what happened by returning or recording typed data

_Reason:_ asserting on a recorded call couples the test to how the code calls, not to what it
achieves — and the recording double is the one that survives a refactor.

```python
# Don't
store.get.assert_called_once_with('flow:42')

# Do
assert await store.get('flow:42') == expected      # a real in-memory store
assert api.calls == (ApiCall('create_post', channel_id='c1'),)   # a recording double
```

_Limits:_ a recording double is still a real implementation of the Protocol; the record is its
output, not a patch on ours.
_Tier:_ `review`, with `ST-TST-01` covering the mechanical part. _Checked in:_ PR.
_From:_ [ADR-0015](../adr/0015-plugin-contract-and-composition.md), [`docs/research/03`](../research/03-bot-framework-architectures.md).

#### `ST-TST-08` — Parametrise one test over the implementations instead of copying it per implementation

_Reason:_ two copies drift, and the copy that drifts is the one for the backend nobody runs locally.

```python
# Don't
def test_memory_cas(): ...
def test_redis_cas(): ...

# Do
@pytest.mark.parametrize('store', ['memory', 'redis'], indirect=True)
async def test_stale_version_returns_conflict(store: KeyValueStore) -> None: ...
```

_Limits:_ an implementation with genuinely different observable behaviour — a capability it declares
unsupported — gets its own test for that difference and shares the rest.
_Tier:_ `review`. _Checked in:_ PR. _From:_ [ADR-0022](../adr/0022-state-plugin-model.md).

#### `ST-TST-09` — Inject the clock and drive time forward; never sleep

_Reason:_ a suite that sleeps is a suite that is slow and flaky at the same time, and every timeout,
TTL and backoff in this design is time-dependent.

```python
# Don't
await asyncio.sleep(1.1)
assert state.expired

# Do
clock = FakeClock()
store = InMemoryKeyValueStore(clock=clock)
clock.advance(SLIDING_TTL + 1)
assert isinstance(await context.load(), StaleState)
```

_Limits:_ no exceptions in unit tests. An integration test against real infrastructure may wait, and
must bound the wait.
_Tier:_ `tool` — pytest configuration (a per-test timeout), `semgrep:ST-TST-09`.
_Checked in:_ LLD, PR. _From:_ [ADR-0022](../adr/0022-state-plugin-model.md), [ADR-0023](../adr/0023-websocket-gateway-resilience.md), [`docs/research/13`](../research/13-conversation-state-lifetime.md).

## 12. Review checklist

Derived from the rules above and from nothing else. Every line names the rules it covers, each
identifier appears on exactly one line of its block, and a line with no rule behind it does not
belong here.

### 12.1 Design review — a component design document

Every rule tagged `LLD`, whatever its tier: at design time no tool has run.

- [ ] The component has one named reason to change; its parts are parts, not second responsibilities, and each module holds one component or one part. `ST-SOL-01`, `ST-MOD-09`
- [ ] Extension happens by adding a Plugin or an implementation, not by a branch in this component; anything admitted to the Core passes the two-condition test. `ST-SOL-02`, `ST-PAT-04`
- [ ] Every seam is a Protocol sized to one consumer, owned by the Core, and every implementation of it passes the conformance suite unchanged. `ST-SOL-03`, `ST-SOL-04`
- [ ] Every dependency runs in the direction of the layer table; a needed import in the wrong direction is resolved as a seam or as deliberate duplication. `ST-SOL-05`, `ST-MOD-04`, `ST-MOD-05`, `ST-MOD-10`
- [ ] Every applied pattern is named as on refactoring.guru with its problem and the rejected alternative; welcome patterns are cited, restricted ones carry an ADR, banned ones are absent; the considered-and-unused list is present. `ST-PAT-01`, `ST-PAT-02`, `ST-PAT-03`, `ST-PAT-09`
- [ ] Collaborators arrive through the constructor, classes are `@final` unless the document names who subclasses them, no state is global, and inheritance appears only where §3 allows it — a closed variant base, the error taxonomy, or a private async/sync `_Base…`. `ST-PAT-05`, `ST-PAT-06`, `ST-PAT-07`, `ST-PAT-08`, `ST-PAT-10`, `ST-TYP-08`
- [ ] The contract has no `Any`, no `cast`, no `TYPE_CHECKING` import and no open signature; values crossing the seam are frozen; annotations are read through the one helper; state is never stashed on a foreign object; an Event is enriched only through `derive`. `ST-TYP-03`, `ST-TYP-04`, `ST-TYP-05`, `ST-TYP-10`, `ST-TYP-11`, `ST-TYP-12`, `ST-TYP-16`, `ST-TYP-17`
- [ ] Post-floor typing names come from the compat module; public generics have typing tests, negative cases included; suppressions appear only in Quarantine and `tests/typing/`. `ST-TYP-09`, `ST-TYP-13`, `ST-TYP-14`
- [ ] A parameter that changes the return type is exposed as an overload on a `Literal`, so the call site declares which contract it wants. `ST-TYP-15`
- [ ] Every task has a named owner in a `TaskGroup`; every I/O await has a named-duration timeout and none wraps `__anext__`; cancellation passes; `shield` appears only in the drain; exception groups lose no sibling. `ST-ASY-01` … `ST-ASY-06`
- [ ] The colour of every callable the framework invokes is stated: synchronous Handlers and Providers are declared and idempotent, everything else is a coroutine function, blocking work goes to `asyncio.to_thread`, and the loop belongs to the application. `ST-ASY-07`, `ST-ASY-08`, `ST-ASY-09`, `ST-ASY-10`, `ST-ASY-12`
- [ ] Each failure the document lists says whether it is a typed outcome or an exception, and which boundary converts it; exhausted alternatives convert at the chain boundary; cardinality matches the mechanism; each failure has one representation. `ST-ERR-01` … `ST-ERR-05`
- [ ] A bad composition stops the start with the full list; unexpected exceptions reach the ErrorBoundary; exceptions carry no content and are rooted at `AiommbotError`, warnings at `AiommbotWarning`, with `retryable` as a property. `ST-ERR-06` … `ST-ERR-10`
- [ ] Every name is its `CONTEXT.md` term, collides with no `_Avoid_` list, and any new concept gets its term in this commit; the `Sync` prefix, the module plural and the type-parameter spellings match the decided ones. `ST-NAM-01`, `ST-NAM-02`, `ST-NAM-03`, `ST-NAM-05`, `ST-NAM-06`, `ST-NAM-07`, `ST-NAM-08`
- [ ] The public surface satisfies all four criteria and everything else is `_internal`; importing any public module needs no extras and no configuration; a missing extra fails at construction. `ST-MOD-01`, `ST-MOD-02`, `ST-MOD-07`, `ST-MOD-08`
- [ ] The document states what is logged and what is not: identifiers only, one logger per component, no content switch, the single redaction list, a correlation id for anything a user sees. `ST-LOG-01` … `ST-LOG-04`, `ST-LOG-06`
- [ ] Every public name the document introduces is documented, its examples are executable, and each Protocol docstring states the implementer's contract and names the conformance suite. `ST-DOC-01`, `ST-DOC-02`, `ST-DOC-03`
- [ ] The testing section names the doubles it uses (never mocks of our own types), the conformance suite each implementation passes, a test per failure mode, and how time is controlled. `ST-TST-01`, `ST-TST-02`, `ST-TST-04`, `ST-TST-09`

### 12.2 Code review — a pull request

Every `review`-tier rule and nothing else: everything `tool` in this document is already red in CI,
and re-checking it by hand is how a checklist stops being read. A rule tagged `LLD` only is checked
when the pull request changes the component's contract or its document.

- [ ] Each touched class still has one reason to change, and each new capability was added rather than branched in. `ST-SOL-01`, `ST-SOL-02`, `ST-PAT-04`
- [ ] Any pattern introduced is named with its rejected alternative; a restricted pattern brought its ADR; the diff introduces no banned pattern; the considered-and-unused list still holds. `ST-PAT-01`, `ST-PAT-02`, `ST-PAT-03`, `ST-PAT-09`
- [ ] New Protocols are sized to one consumer; collaborators arrive through the constructor; new classes are `@final` unless documented otherwise; new shared behaviour is not a mixin outside a private async/sync base; a new closed set of alternatives is a base with frozen members. `ST-SOL-04`, `ST-PAT-05`, `ST-PAT-07`, `ST-PAT-08`, `ST-PAT-10`, `ST-TYP-08`
- [ ] Constants are `Final[<type>]`, cite their source where they come from one, and no duration is a literal at a call site. `ST-TYP-01`, `ST-DOC-05`, `ST-ASY-02`
- [ ] A parameter that changes the return type is an overload on a `Literal`, not a boolean. `ST-TYP-15`
- [ ] No timeout wraps `__anext__`; a bounded queue sits between producer and consumer; exception groups keep their siblings; the loop is still the application's. `ST-ASY-03`, `ST-ASY-06`, `ST-ASY-07`
- [ ] A new synchronous Handler is idempotent; a new `async def` with no `await` implements an async contract; blocking work goes to `asyncio.to_thread`, not to the Sync executor. `ST-ASY-09`, `ST-ASY-11`, `ST-ASY-12`
- [ ] Every new failure is an outcome or an exception by the rule, converted at a boundary, with the cardinality the mechanism implies, one representation and no payload; retryability is read, not recomputed. `ST-ERR-01`, `ST-ERR-02`, `ST-ERR-03`, `ST-ERR-04`, `ST-ERR-05`, `ST-ERR-08`, `ST-ERR-10`
- [ ] No handler swallows an exception it did not expect. `ST-ERR-07`
- [ ] Names are glossary terms, collide with no `_Avoid_` list, any new concept arrives with its term in this commit, and a new module is singular or plural by what it holds. `ST-NAM-01`, `ST-NAM-02`, `ST-NAM-03`, `ST-NAM-06`, `ST-NAM-07`, `ST-NAM-08`
- [ ] Every configured exception — import contract, lint relaxation, slotscheck exclusion, switched-off rule — carries its reason. `ST-MOD-06`
- [ ] A deferred import exists only in the constructor of an object needing an optional extra. `ST-MOD-08`
- [ ] Log lines carry identifiers and not content, no content switch was added, and the redaction list was not bypassed; user-visible failures carry a correlation id. `ST-LOG-01`, `ST-LOG-02`, `ST-LOG-03`, `ST-LOG-06`
- [ ] Comments explain why and cite the source; a `TODO:` names an issue; a public API change records its version. `ST-DOC-04`, `ST-DOC-06`
- [ ] New tests assert one behaviour each, are parametrised over implementations rather than copied, cover the failure modes the document lists, and report through returned data rather than recorded calls. `ST-TST-03`, `ST-TST-04`, `ST-TST-07`, `ST-TST-08`
- [ ] A Protocol docstring changed with its contract still states the implementer's contract and names the conformance suite that applies. `ST-DOC-03`
