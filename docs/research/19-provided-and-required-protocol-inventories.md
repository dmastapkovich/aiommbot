# 19. Provided and required Protocols in an inventory

**Question.** Our Core owns a set of Protocols that share one shape: the framework calls out
through them and an outside party supplies the implementation. `ReplyChannel[R]` has the opposite
shape — the framework hands user code an object typed by it, and user code calls it. Is that the
same kind of thing, and does an architecture document that inventories such Protocols mark the
difference?

Gathered for [#84](https://github.com/dmastapkovich/aiommbot/issues/84) from three angles: what
mature Python libraries do (§1), what architecture doctrine says (§2), and what the shape of our
own catalogue implies about how the inventory ages (§3). Findings only — the decision is
[ADR-0038](../adr/0038-seam-inventory-records-the-direction-of-the-call.md).

Sources were read on 2026-09-08. Library claims come from a shallow clone of each default branch
plus the documentation that ships inside the same repository. Anything that could not be reached is
marked **UNVERIFIED** where it appears.

## 1. What the ecosystem does

### 1.1 The comparison

| Project | Handed-out capability | How typed | Substitutable? | Same inventory as the pluggable backends? |
|---|---|---|---|---|
| Slack Bolt | `say`, `respond`, `ack`, `complete`, `fail` | Concrete classes with `__call__`. `grep -rn "Protocol" slack_bolt/` returns **zero** hits | No shipped double; the suite drives a real `App` against a local mock Slack server | **No** — "listener arguments" under a bare `# utilities` comment in `Args`; the pluggable side is "adapters", its own pair of doc pages |
| discord.py | `Interaction.response` → `InteractionResponse` | Concrete `Generic` class with `__slots__`, deliberately **outside** `discord.abc` | No | **No** — `docs/interactions/api.rst`; the "Abstract Base Classes" section holds only `Snowflake`, `User`, `PrivateChannel`, `GuildChannel`, `Messageable`, `Connectable` |
| python-telegram-bot | `context: CallbackContext` | Concrete `Generic[BT, UD, CD, BD]`. The whole package has four `Protocol`s, all private helpers | By **class replacement**: `ContextTypes(context=MyContext, …)` | **No** — its own page; the pluggable ports get inheritance-tree index pages |
| aiogram 3.31 | `state: FSMContext`, `bot: Bot` | Plain concrete class wrapping a `BaseStorage` | The **port behind it** is (`BaseStorage(ABC)`), never `FSMContext` itself. `MockedBot` is in `tests/`, outside the package | **No** — handler inputs are a `TypedDict` hierarchy (`MiddlewareData`); ports are ABCs under `docs/api/session/` |
| Starlette / FastAPI | `Request`, `Response`, `WebSocket`, `BackgroundTasks` | Concrete classes. Starlette's only `Protocol`s are two private ones | One level up: `TestClient`, and `app.dependency_overrides` keyed by the **function object** | No inventory of extension points exists in either project |
| Litestar | `request`, `socket`, `state`, `scope`, `headers`, `cookies`, `query`, `body` | Concrete `Generic` classes; the set is `Final` in `litestar.constants.RESERVED_KWARGS` | No double for `Request`; Litestar *does* ship one for a port (`generic_mock_repository`) | **No, and the split is explicit** — "reserved keyword arguments" in the handler docs vs "Plugins are defined by protocols" in the plugin docs |
| FastStream | `Context(...)` values; handler returns `faststream.Response` | `Response` is a plain concrete class. The driven ports are `Protocol` en masse: `ProducerProto`, `ParserProto`, `DecoderProto`, `PublisherProto`, `LoggerProto` | The **broker** is: `TestRabbitBroker`, `TestKafkaBroker` | **No**; the ports live under `_internal/` and are not public surface |
| Temporal Python SDK | `activity.info()`, `activity.heartbeat()`, `activity.client()` | **Not an object at all** — module functions over a `ContextVar`-held private `_Context` | By installing the ambient context: `testing.ActivityEnvironment` | **No**; extension points are `temporalio/plugin.py` |
| pytest | `monkeypatch`, `capsys`, `caplog`, `tmp_path` | Concrete classes (`MonkeyPatch`, `CaptureFixture`). The three `Protocol`s in `_pytest/` are private | They *are* the doubles; `MonkeyPatch` is directly constructible standalone | **No — a three-way split**, see §1.2 |
| Trio | `MemorySendChannel`, subprocess stdin `SendStream` | `trio.abc.SendChannel[T]` — **`abc.ABC` + `@abstractmethod`**, generic in the item type | **Yes, fully**: `trio.testing.MemorySendStream` plus a shipped conformance suite (`check_one_way_stream`, `check_two_way_stream`, `check_half_closeable_stream`) | **Partly** — one `trio.abc` namespace, but the docs split it, see §1.3 |
| AnyIO | `MemoryObjectSendStream` | `anyio.abc.ObjectSendStream[T]` — ABC, docstring "An interface for sending objects." | Shipped in-process implementation; **no** `check_*` conformance functions in the source | One `anyio.abc` namespace; docs split by topic, not by category |
| ASGI spec | the `send` / `receive` callables | **Neither Protocol nor ABC** — prose, "an awaitable callable taking a single event dictionary"; Starlette encodes bare `Callable` aliases | Informal ecosystem doubles; nothing normative | The spec does not list them as "interfaces" alongside anything |

### 1.2 Four projects name the split in their own vocabulary

**pytest** is the sharpest: `doc/en/reference/reference.rst` opens with three top-level sections.

> **Fixtures** — "Fixtures are requested by test functions or other fixtures by declaring them as argument names."
>
> **Hooks** — "Reference to all hooks which can be implemented by `conftest.py` files and plugins."
>
> **Objects** — "Objects accessible from fixtures or hooks or importable from `pytest`."

*What you are given* / *what you implement* / *the types of what you are given*.
`pytest.MonkeyPatch` and `pytest.CaptureFixture` are autodoc'd under **Fixtures**, not Hooks.

**Litestar** — the two phrases live on two pages and never mix:

> `docs/usage/routing/handlers.rst`: "you can specify the following special kwargs, (known as **"reserved keywords arguments"**)"
>
> `docs/usage/plugins/index.rst`: "**Plugins are defined by protocols**, and any type that satisfies a protocol can be included in the `plugins` argument of the app."

The reserved set is a code constant — `RESERVED_KWARGS: Final = {"state", "headers", "cookies",
"request", "socket", "data", "query", "scope", "body"}`.

**Slack Bolt** — "listener arguments" for what a listener receives, "adapters" / "custom adapters"
for the pluggable side, with a page each.

**discord.py** scopes its ABC module to identity rather than capability:

> "An abstract base class … is a class that models can inherit to get their behaviour. **Abstract base classes should not be instantiated.** They are mainly there for usage with `isinstance` and `issubclass`."

`InteractionResponse` — the actual reply channel — is **not** in that module or that docs section.

### 1.3 Trio: two categories in one namespace, still separated by the docs

`trio.abc` exports both kinds, and the docstrings carry the category:

- `class Clock(ABC)`: "The interface for custom run loop clocks."
- `class HostnameResolver(ABC)`: "**If you have a custom hostname resolver**, then implementing `HostnameResolver` allows you to register this to be used by Trio."
- `class Instrument(ABC)`: "Instruments don't have to inherit from this abstract base class … **This class serves mostly as documentation.**"

The pluggable ones say "if you have a custom X, register it"; the stream and channel ones say what
the object *is*. The docs place them apart: streams and channels get the "Abstract base classes"
list-table in `reference-io.rst` — whose overview table carries an **"Example implementations"**
column pointing at `trio.testing.MemorySendStream` — while `Instrument` goes to
`reference-lowlevel.rst` and `Clock` to `reference-testing.rst`.

Trio is the only sampled project that types a handed-out capability as an interface *and* ships a
conformance suite for it. The justification is not the handing-out: `reference-io.rst` says the
interface exists so "it lets you write generic protocol implementations that can work over
arbitrary transports" — many independent implementations, the classic driven-port case. In Trio and
AnyIO a channel is a peer-to-peer primitive that user code creates itself; nothing hands it in.

### 1.4 The nearest semantic match is a concrete class

discord.py's `InteractionResponse` has all three of `ReplyChannel`'s distinguishing traits:

- single use — `is_done()`, "An interaction can only be responded to once";
- a typed already-answered outcome — `InteractionResponded`, raised at 15 call sites;
- a deadline — `Interaction.expires_at = created_at + timedelta(minutes=15)`, plus `is_expired()`.

It is a concrete `Generic` class outside `discord.abc`, with no double and no conformance suite.
The option is closed to us: [ADR-0032](../adr/0032-layer-model-and-direction-of-allowed-dependencies.md)
forbids the Core to name the Webhook plugin's reply types, so the slot's type must be a Protocol.

### 1.5 Three observations

1. **`Protocol` usage tracks who calls whom, not who is handed what.** Across the sample,
   `Protocol` and ABC are used almost exclusively for *the framework calls you* — Bolt
   `Middleware`, aiogram `BaseStorage`, PTB `BasePersistence`/`BaseRequest`, Litestar
   `Store`/`*Plugin`, FastStream `ProducerProto`, Trio `Clock`/`HostnameResolver`. Every *you call
   it* capability in the sample is a concrete class, Trio's streams excepted.
2. **When a handed-out object must be swapped, the projects swap something else** — aiogram the
   storage behind `FSMContext`, FastStream the broker, FastAPI the provider function, Temporal the
   ambient context, PTB the class itself.
3. **Every project that maintains a real inventory keeps two lists**, and **no project in the
   sample puts a handed-out capability into the same table as its pluggable backends.**

## 2. What the doctrine says

### 2.1 Four doctrines split, three flatten

**Cockburn, hexagonal architecture.** The section is named for the asymmetry —
*The Left-Right Asymmetry* — and it is candid that the one-kind treatment is a fiction:

> "The ports and adapters pattern is deliberately written pretending that all ports are fundamentally similar."
>
> "That pretense is useful at the architectural level. In implementation, ports and adapters show up in two flavors."
>
> "The distinction between primary and secondary lies in who triggers or is in charge of the conversation."

The "application offers this API" side is the primary/driving one — "Imagine now that every piece
of functionality the application offers were available through an API". His documentation treatment
is **spatial separation inside one diagram**: "The primary ports and primary adapters on the left
side (or top) of the hexagon, and the secondary ports and secondary adapters on the right (or
bottom) side." The split has operational teeth: FIT for a primary actor, a mock for a secondary one.
He names no category for an object handed *back* to the driver (**UNVERIFIED** — no such passage
exists); by his stated criterion it lands on the primary side.

**UML** is the sharpest vocabulary, and the structurally decisive point is that `provided` and
`required` are **two derived properties of one port**:

> "A port may specify the services an encapsulated classifier provides to its environment as well as the services that an encapsulated classifier requires of its environment."
>
> "The provided interfaces of a port describe requests to the classifier that other classifiers may make through this port."
>
> "The required interfaces of a port describe the requests that may be made from the classifier to its environment through the port."

Different derivation mechanisms (realization vs usage dependency), different glyphs (lollipop vs
socket), **one diagram**. UML never splits them into separate model elements and never renders them
identically. Our eleven are required interfaces; the twelfth is a provided one. (**UNVERIFIED**: the
OMG PDF could not be opened in the sandbox; `uml-diagrams.org` reproduces the spec wording, and the
attribution of these derived properties to clause 11.3 is unconfirmed.)

**Clean Architecture** names them Input Port and Output Port, and the subtle part is *why*: Martin
discriminates by **flow of control precisely because source-dependency direction is deliberately
made uniform** — "We take advantage of dynamic polymorphism to create source code dependencies that
oppose the flow of control". In his scheme, which way the import points cannot classify an
interface. (**UNVERIFIED**: the fetched prose attests "Output Port" explicitly; "Input Port" appears
as a figure label.)

**DDD** makes what we publish a differently *named pattern*: Open Host Service and Published
Language are upstream-only, against Anticorruption Layer and Conformist downstream. Not one list
with two entries — two patterns.

**C4 flattens**: "A component is a grouping of related functionality encapsulated behind a
well-defined interface" — singular, undifferentiated, no ball-and-socket, and the component-diagram
page carries no interface guidance at all. Its FAQ concedes our exact case: "To document a library,
framework or SDK, you might be better off using something like UML."

**Feathers' "seam"** — the word our table already uses — is direction-neutral by definition: "a
place where you can alter behavior in your program without editing in that place", split by
mechanism (preprocessing, link, object), never by direction.

**arc42 abstains rather than flattens.** Its §5 white-box template has an optional "important
interfaces" slot and no format for it: "Since there are so many ways to specify interfaces why do
not provide a specific template for them" *(sic)*. Tip 5-21's four graduated levels of interface
detail are no explanation → semantics → technical details → quality attributes; **none of the four
is "who implements it."** But arc42's FAQ B-5 does use the dichotomy, splitting "where to document
external interfaces" into provide and consume with a different obligation each.

### 2.2 The mapping

| Doctrine | The eleven | The twelfth | Word for the difference |
|---|---|---|---|
| Cockburn | secondary / driven ports | **primary / driving** — an "advertised function" | primary vs secondary; who is in charge of the conversation |
| UML 2.5 | **required** (usage dependency, socket) | **provided** (realized, lollipop) | provided vs required — the oldest formal pair |
| Clean Architecture | output-port-shaped | input-port-shaped | Input vs Output Port, by flow of control |
| DDD strategic | downstream | **Open Host Service** / Published Language | upstream vs downstream, different patterns |
| arc42 | FAQ B-5's "interfaces provided by external systems" | FAQ B-5's "external interfaces to external consumers" | yes in the FAQ, none in the templates |
| C4 | "well-defined interface" | same word | none |
| Feathers | object seam | object seam | none — direction-neutral |

### 2.3 The cross-cutting finding

Every doctrine that distinguishes uses the **same** discriminator: direction of the call, who is in
charge of the conversation. **None discriminates on who supplies the implementation.**

That is the finding the evidence forces, and it is about our table rather than about the twelfth
row. §5.4's *title* organises on substitutability ("seams", which by Feathers' direction-neutral
definition admits the twelfth) while its *introduction* organises on the supply side ("who
implements it") and asserts dependency inversion (which excludes the twelfth). The two statements
were already in tension with each other; the twelfth Protocol only made the tension visible.

**Not found:** no canonical guidance anywhere on "one table with a discriminator column" versus
"two tables" — no arc42 tip, no C4 page, no ADR-community text. The only published precedent
located is Elastic Path's extension-point framework, which uses **separate sections per category**
(Data Source · Events · Metadata · Logic). Nygard's model is relevant for a different reason:
"interfaces" is in his own list of what makes a decision architecturally significant, and his scheme
makes the classification *rule* the durable artefact with the table as a derived view.

## 3. How our own inventory ages

### 3.1 Census

Fourteen Core-owned Protocols, in three classes by who calls and who implements.

| Class | Members | In §5.4 before #84 |
|---|---|---|
| **required** — the Core calls out, an outside party implements | `Transport`, `DependencyProvider`, `KeyValueStore`, `LockProvider`, `Codec`, `HTTPTransport`, `SyncHTTPTransport`, `WebSocketConnection`, `StateKeyProvider`, `TokenProvider`, `SyncTokenProvider`, `CallbackTokenCodec`, `RequestObserver` | all — thirteen Protocols on eleven rows |
| **contribution** — the Core calls, a Plugin implements, arbitrarily many instances | `ContributesRouters`, `ContributesMiddleware`, `ContributesDependencies`, `ContributesEventTypes`, `ContributesChecks`, `HasLifecycle` | **none — and no §5 row at all**, not even as a named part |
| **provided** — the Core hands the object to user code, user code calls it | `ReplyChannel[R]` | no |

Two further contracts sit outside the Core's ownership and stay out of §5.4 on that ground: the
IdentityCache Protocol is **Adapter-owned** (§5.8 states the reason in the row itself), and
`Filter`, `Extractor`, `Middleware`, `Provider` and `Check` are ranked as components or parts.

So §5.4 was never "every Protocol the Core owns", whatever its prose said — six `Contributes*`
Protocols are Core-owned public API under semver and appear in no §5 row.

### 3.2 The forecast: `ReplyChannel` is probably exactly one, forever

The generator is narrow and conjunctive: **a Core-owned data type must have a field whose value is
supplied from a higher layer and is *called*, not merely read, by user code.** Everything else that
reaches a Handler arrives through type-keyed dependency injection
([ADR-0018](../adr/0018-core-owned-type-keyed-dependency-injection.md)), and that mechanism removes
the need for a Protocol: the key *is* the concrete type its owner registers, so the Core never has
to name it. ADR-0036 explicitly **rejected** the injectable route for the reply slot, which is what
forced this one case out of DI and into a Protocol.

Supporting facts:

- `EventMeta`'s field list is closed and enumerated — five plain-data fields, exactly one callable.
- [ADR-0037](../adr/0037-derive-is-the-only-enrichment-path-for-an-event.md) has just frozen the
  envelope: "`Event` carries exactly one method. Everything else about it is data."
- Every other Core-owned type is data — `HandlerSpec`, `Outcome`, `Check`, `ProcessProfile`,
  `PluginSpec`, `MatchedHandler`, `Flag`, `Resolution plan`. The one holding a callable, `Provider`,
  holds it so the *framework* can call it.
- Every named candidate fails on ownership or on shape. `Runtime`, `Workspace` and `StateContext`
  are Adapter- or plugin-owned concrete classes — ADR-0035 names the Core-depends-on-Adapter-through
  -injectable-`Runtime` reading as the contradiction its ordering rule exists to avoid. `Flag` is the
  cleanest counter-example: the Core stores objects of types it does not know, by type, and needs no
  Protocol because it never calls them. "The Core holds a foreign value" does not by itself produce
  a Protocol.
- The one realistic growth path adds no row: a second request/response Transport reuses
  `ReplyChannel[R]` with a new `R`, exactly as `ActionReply` and `DialogReply` already share one
  Protocol. The Protocol is generic in the reply type so that new reply values are new type
  arguments, not new seams.

**The larger latent population is on the other side.** If the inventory ever admits a second class
of row keyed on *who implements*, the six `Contributes*` Protocols have as much claim as anything —
six members, not one. A discriminator keyed on *who calls* leaves them exactly where they are,
beside the eleven.

### 3.3 What §5.4 already tolerates

Three of the supposedly distinguishing traits are already in the table:

- `RequestObserver` is plural, application-implemented, and its shipped implementations read "none
  by default; a first-party extra".
- `TokenProvider` and `SyncTokenProvider` read "none — the application's".
- Seam rows and part rows already coexist for the same Protocol in five cases —
  `StateKeyProvider`, the transport and token Protocols, `WebSocketConnection`. Both of
  `ReplyChannel`'s part rows were already written, in §5.5 for `event.md` and §5.8 for `webhook.md`.

Whatever makes `ReplyChannel` different, it is not "many instances", not "the application
implements it" and not "it is also a part somewhere". It is the direction of the call, and nothing
else.

### 3.4 A third exception to the §5.4 prose

[ADR-0035](../adr/0035-lld-order-is-a-topological-sort-of-structural-contract-dependencies.md) found
the prose "a Protocol is specified inside the document of the component that consumes it" false for
five of eleven rows, where the seam is named after its implementation and the document is the
implementation's: `DependencyProvider`, `KeyValueStore`, `LockProvider`, `Codec`,
`CallbackTokenCodec`.

`ReplyChannel` breaks it a **third** way. Its *Specified in* is `event.md`, which is neither the
consumer's document — the consumer is the Handler, user code, which has no document — nor the
implementation's, `webhook.md`. It is the document of the component that types the field holding it.
A twelfth row makes the prose false for six of twelve rows, for two distinct reasons.

## Sources

Library sources, shallow clone of the default branch, 2026-09-08:

- Slack Bolt for Python — <https://github.com/slackapi/bolt-python> — `slack_bolt/context/say/say.py`,
  `context/ack/ack.py`, `context/respond/respond.py`, `kwargs_injection/args.py`,
  `middleware/middleware.py`, `docs/english/concepts/custom-adapters.md`,
  `docs/english/concepts/message-sending.md`
- discord.py — <https://github.com/Rapptz/discord.py> — `discord/abc.py`, `discord/interactions.py`,
  `discord/errors.py`, `docs/api.rst`, `docs/interactions/api.rst`
- python-telegram-bot — <https://github.com/python-telegram-bot/python-telegram-bot> —
  `src/telegram/ext/_callbackcontext.py`, `_contexttypes.py`, `_basepersistence.py`,
  `src/telegram/request/_baserequest.py`, `docs/source/telegram.ext.callbackcontext.rst`
- aiogram 3.31 — <https://github.com/aiogram/aiogram> — `aiogram/fsm/context.py`,
  `aiogram/fsm/storage/base.py`, `aiogram/client/session/base.py`,
  `aiogram/dispatcher/middlewares/data.py`, `tests/mocked_bot.py`
- Starlette — <https://github.com/encode/starlette> — `starlette/types.py`
- FastAPI — <https://github.com/fastapi/fastapi> — `docs/en/docs/advanced/testing-dependencies.md`
- Litestar — <https://github.com/litestar-org/litestar> — `litestar/constants.py`,
  `litestar/plugins/base.py`, `litestar/stores/base.py`, `docs/usage/routing/handlers.rst`,
  `docs/usage/plugins/index.rst`
- FastStream — <https://github.com/airtai/faststream> — `faststream/response/response.py`,
  `_internal/parser.py`, `_internal/producer.py`, `_internal/testing/broker.py`
- Temporal Python SDK — <https://github.com/temporalio/sdk-python> — `temporalio/activity.py`,
  `temporalio/testing/_activity.py`, `temporalio/plugin.py`
- pytest — <https://github.com/pytest-dev/pytest> — `doc/en/reference/reference.rst`,
  `src/_pytest/monkeypatch.py`, `src/_pytest/capture.py`
- Trio — <https://github.com/python-trio/trio> — `src/trio/_abc.py`, `docs/source/reference-io.rst`,
  `reference-testing.rst`, `reference-lowlevel.rst`
- AnyIO — <https://github.com/agronholm/anyio> — `src/anyio/abc/_streams.py`, `docs/streams.rst`

Specifications and doctrine:

- ASGI specification — <https://asgi.readthedocs.io/en/latest/specs/main.html>
- Alistair Cockburn, *Hexagonal Architecture (Ports and Adapters)* —
  <https://alistair.cockburn.us/hexagonal-architecture/>
- OMG *Unified Modeling Language* 2.5.1 — <https://www.omg.org/spec/UML/2.5/PDF> (not opened;
  wording read from <https://www.uml-diagrams.org/port.html> and
  <https://www.uml-diagrams.org/component.html>)
- Robert C. Martin, *The Clean Architecture* —
  <https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html>
- DDD Open Host Service and Published Language — <https://contextmapper.org/docs/open-host-service/>,
  <https://contextmapper.org/docs/published-language/>
- arc42 §5 — <https://docs.arc42.org/section-5/>; FAQ B-5 — <https://faq.arc42.org/questions/B-5/>;
  Tip 5-1 — <https://docs.arc42.org/tips/5-1/>; Tip 5-21 — <https://docs.arc42.org/tips/5-21/>
- C4 model, Component and FAQ — <https://c4model.com/abstractions/component>,
  <https://c4model.com/faq>
- Michael Feathers, *Working Effectively with Legacy Code*, seam types —
  <https://www.informit.com/articles/article.aspx?p=359417&seqNum=3>
- Michael Nygard, *Documenting Architecture Decisions* —
  <https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions>
- Elastic Path Extension Point Framework —
  <https://documentation.elasticpath.com/extension-framework/docs/extension-points/index.html>

Marked **UNVERIFIED** in place: Cockburn's current page against the 2005 original (web.archive.org
blocked); the OMG PDF and its clause attribution; Martin's "Input Port" as prose rather than a
figure label; Django's placement of custom-backend how-tos; whether AnyIO ships conformance
checkers (`grep -rn "def check_" src/anyio/` finds none, but absence was not confirmed against the
docs); Bolt shipping no official test kit.
