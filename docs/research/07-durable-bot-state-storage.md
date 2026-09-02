# Durable state storage for chat bots: industry practice

Research date: 2026-09-02. Sources are primary (framework source on GitHub, official docs).
Claims I could not confirm from a primary source are marked **[unverified]** or
**[best-effort, low confidence]**.

## 1. Comparison table

| Framework | Ships storage? | First-party backends | FSM vs. user data | Lock / CAS | TTL | Test strategy |
|---|---|---|---|---|---|---|
| aiogram 3 | Yes | Memory, Redis, Mongo (`PyMongoStorage`) | Separate (`set_state` vs `set_data`, same key) | `BaseEventIsolation.lock()` (Memory/Redis) | Redis only | Shared `TestStorages`, parametrized over 4 backends |
| python-telegram-bot | Yes (interface + 2 impls) | `PicklePersistence`, `DictPersistence` | No FSM concept; one blob | None; docstring warns of races | None | No shared suite; per-class tests |
| Slack Bolt (Python) | OAuth only | File, SQLite3, SQLAlchemy (`slack_sdk`) | N/A — no FSM store | `consume()` deletes-on-read | OAuth-state only | No conversation-state toolkit (issue #380 open) |
| MS Bot Framework SDK | Yes | Memory, CosmosDB, Blob | No FSM primitive; undifferentiated `Storage` | eTag CAS (`"*"` = force) | None built-in | Community adapters, no shared upstream suite |
| Rasa | Yes (2 stores) | `TrackerStore`: Memory/SQL/Redis/**Mongo**/Dynamo; `LockStore`: Memory/Redis | Explicitly separate stores | `LockStore` ticket queue | None | Shared parametrize over 4 tracker backends |
| Botkit v4 (JS) | No own abstraction | Delegates to Bot Framework `Storage` | Same as Bot Framework | Same (eTag) | None | Inherits Bot Framework's tests |
| Botpress (ADK, JS/TS) | Yes, opaque | Undisclosed | Bot/user/conversation scopes | Undocumented | Undocumented | **(best-effort, low confidence)** |
| discord.py | No | None | N/A | N/A | N/A | Community aiosqlite/asyncpg, per maintainers |
| aiogram-dialog | No new layer | Reuses aiogram's storage/isolation | Stack+context on FSM data field | Reuses aiogram's lock | Reuses aiogram's | Not separately investigated |

## 2. Framework-by-framework findings

### 2.1 aiogram 3 — `aiogram.fsm.storage`

`BaseStorage` (`aiogram/fsm/storage/base.py`): `set_state`/`get_state`, `set_data`/`get_data`/`update_data`, `get_value`, `close`. Keys are `StorageKey(bot_id, chat_id, user_id, thread_id, business_connection_id, destiny="default")`, turned into a string by a `KeyBuilder` (`DefaultKeyBuilder`: `fsm:<bot_id?>:<chat_id>:<user_id>:<destiny?>:<part>`, `part ∈ {"state","data","lock"}`). Locking is a separate axis: `BaseEventIsolation.lock(key)` (`SimpleEventIsolation` = in-process `asyncio.Lock` dict; `RedisEventIsolation` = cross-replica).

Mongo support (`MongoStorage`, Motor-based) is community-contributed: [PR #841](https://github.com/aiogram/aiogram/pull/841) (2022-02-18, `3.x future` milestone). [aiogram 3.22.0](https://github.com/aiogram/aiogram/pull/1705) (17 Aug 2025) deprecated it for `PyMongoStorage`, dropping `motor` for PyMongo's own `AsyncMongoClient`. `PyMongoStorage.update_data` uses `find_one_and_update()`; neither Mongo storage configures a TTL index. Only `RedisStorage` has `state_ttl`/`data_ttl`.

`tests/test_fsm/storage/test_storages.py` defines a shared `TestStorages` class (`test_set_state`, `test_set_data`, `test_update_data`, …) run via `@pytest.mark.parametrize` against memory/redis/mongo/pymongo fixtures — a real conformance suite, not four independent test files. No separate `aiogram_scenes` package exists — Scenes ships in core (`fsm/scene.py`) on the same `BaseStorage`/`StorageKey`.

### 2.2 python-telegram-bot — `BasePersistence`

`BasePersistence` (`src/telegram/ext/_basepersistence.py`) defines per-category methods: `get/update/refresh/drop_user_data`, the same trio for `chat_data`, `get/update/refresh_bot_data`, `get/update_callback_data`, `get/update_conversations`, `flush()`; a `PersistenceInput` dataclass toggles which categories persist. PTB has **no FSM primitive**: `ConversationHandler` states live in the same generic `conversations` mapping as everything else. The docstring flags the concurrency gap directly: "this method may be called while a handler callback is still running. This might lead to race conditions" — no lock or CAS anywhere in the contract.

First-party implementations are `PicklePersistence` (one combined pickle file, or 5 separate files; no write locking documented) and `DictPersistence` ("mainly intended as starting point for custom persistence classes," not production). SQL/Redis/Mongo are **community only** — `ptbcontrib` (Postgres/SQLAlchemy, Mongo in its CI) or independent packages like `LucaSforza/MongoPersistence`. Core serialization is pickle, not JSON — a real difference from aiogram/Rasa.

### 2.3 Slack Bolt — `InstallationStore` / `OAuthStateStore`

Bolt does not define these itself — both live in `slack_sdk/oauth/` (Bolt's "Single Dependency Rule": core depends only on `slack_sdk`, per doc 03). `InstallationStore` (`installation_store/installation_store.py`): `save`/`save_bot`/`find_bot`/`find_installation`/`delete_bot`/`delete_installation`/`delete_all`, backends under `{file,sqlite3,sqlalchemy,amazon_s3}/`. `OAuthStateStore` (`state_store/state_store.py`): `issue() -> str` / `consume(state) -> bool`, same backend set plus `stateless` (cookie-based). The `sqlite3` implementation shows the pattern: `consume()` runs `SELECT ... WHERE expire_at > ?` then deletes the row — TTL check plus single-use deletion in one operation, a minimal compare-and-consume, not a general lock.

**Neither Bolt nor `slack_sdk` ships any storage for conversation/FSM state** — confirmed in doc 03 ("None; state is user-land"). No test toolkit for conversation-shaped state exists either (issue #380 still open).

### 2.4 Microsoft Bot Framework SDK — `Storage`

`Storage` (`botbuilder-core/botbuilder/core/storage.py`): `read(keys)`, `write(changes)`, `delete(keys)` over `StoreItem`s carrying an optional `e_tag`. `MemoryStorage.write()` shows the CAS contract: if incoming and stored `e_tag` are both set and differ, raise `KeyError("Etag conflict...")`; `"*"` bypasses the check; empty string is rejected. `CosmosDbPartitionedStorage` implements the same contract against Cosmos: existing items get `upsert_item(..., match_condition=MatchConditions.IfNotModified)`, new items an unconditional `upsert_item()` — optimistic concurrency is native to the interface, not per-backend.

`Storage` is backend-agnostic key/blob storage with no FSM concept; `ConversationState`/`UserState` are a naming convention on top. No first-party Mongo backend exists — the community Bot Builder Community repo ships Mongo/DynamoDB/Redis adapters (e.g. `sebsylvester/botbuilder-storage`, adding configurable TTL, a capability the core interface doesn't define).

### 2.5 Rasa — `TrackerStore` and `LockStore`

`TrackerStore` (`rasa/core/tracker_store.py`), "common behavior and interface for all TrackerStores": `save`, `retrieve`, `retrieve_full_tracker`, `stream_events` (diffs to an optional `EventBroker`), `keys`, `exists`. Same file: `InMemoryTrackerStore`, `SQLTrackerStore` (SQLite/Postgres/MySQL/Oracle), `RedisTrackerStore`, **`MongoTrackerStore`**, `DynamoTrackerStore`, `FailSafeTrackerStore` (falls back to in-memory), `AwaitableTrackerStore`. Mongo is **first-party** here, unlike PTB/Bolt. It creates one non-unique index (`create_index("sender_id")`) and writes via `update_one(..., upsert=True)`; no TTL index, no change streams anywhere in the file.

`LockStore` (`rasa/core/lock_store.py`) is a genuinely separate abstraction: `create_lock`/`get_lock`/`save_lock`/`delete_lock`, `issue_ticket(conversation_id, lock_lifetime)`, `is_someone_waiting`, `lock()`. Rasa's docs state why plainly: "Messages that are being processed lock Rasa for a given conversation ID to ensure that multiple incoming messages for that conversation do not interfere with each other," via a "ticket lock mechanism ... processed in the right order" (`docs/docs/lock-stores.mdx`) — a webhook retry must not let two workers process the same `sender_id` concurrently even though both `retrieve()` the same snapshot. Only `InMemoryLockStore`/`RedisLockStore` exist; there is no Mongo lock store — locking atomicity never rides on `MongoTrackerStore`.

`tests/core/test_tracker_stores.py` runs `@pytest.mark.parametrize("tracker_store_type", [MockedMongoTrackerStore, SQLTrackerStore, InMemoryTrackerStore, ...])` across shared test bodies — the same conformance pattern as aiogram, arrived at independently.

### 2.6 Botpress and Botkit (best-effort)

**Botkit v4** (`howdyai/botkit`, JS): its docs state Botkit "no longer provides an interface for connecting to or using databases," and its `storage` option is "a Storage interface compatible with this specification" — a direct pointer to Bot Framework's `Storage` (§2.4), defaulting to `MemoryStorage` (`packages/docs/reference/core.md`). Botkit v3 had its own storage layer; v4 dropped it for Bot Framework's contract wholesale — convergence on one interface rather than two.

**Botpress** is JS/TS, now a managed platform (ADK) — **(best-effort, low confidence)**. Current docs (`botpress.com/docs/adk-v2/conversations/state`) describe bot/user state (Zod schemas in `bot.config.ts`) and conversation state, "saved automatically." The underlying database is not published in docs I could reach; the superseded v11.x generation used a KVS backed by SQLite/Postgres, but I did not verify the ADK's actual backend from source.

### 2.7 discord.py — no persistence layer

discord.py ships no persistence abstraction — confirmed on the repo's own forum: [discussion #9180](https://github.com/Rapptz/discord.py/discussions/9180) answers "you'd store this data inside a database such as sqlite or postgresql. Use async libraries ... like asqlite/aiosqlite and asyncpg." Bring your own async SQL client; nothing FSM- or KV-shaped ships in the library, and no `ptbcontrib`-style community-blessed package fills the gap.

### 2.8 aiogram-dialog / aiogram_scenes (best-effort)

`aiogram_scenes` is not a real package (§2.1). `aiogram-dialog` (`Tishka17/aiogram_dialog`) is real and adds **no new storage backend**: its `StorageProxy` (`src/aiogram_dialog/context/storage.py`) wraps aiogram's own `BaseStorage`/`BaseEventIsolation`, calling `set_data`/`get_data` with `destiny`-prefixed keys (`"aiogd:context:{intent_id}"`, `"aiogd:stack:{stack_id}"`) to persist a navigation stack and per-screen context as ordinary FSM data — evidence that one well-designed `BaseStorage` contract is generic enough to carry a dialog-navigation layer without its own persistence code.

## 3. The common storage contract

Across every framework with a real storage abstraction (aiogram, PTB, Bot Framework, Rasa), the same shape recurs:

- **Scoped key, not a flat string.** aiogram's `StorageKey(bot_id, chat_id, user_id, thread_id, destiny)`, PTB's per-category id maps, Rasa's `sender_id`, Bot Framework's partition-friendly string key all encode composite identity (who + where + which conversation). aiogram's `KeyBuilder` is the only seam found that makes this composition swappable independent of the backend.
- **get/set/delete, mostly single-key.** `BaseStorage.get_data/set_data`, `Storage.read/write/delete`, `TrackerStore.retrieve/save`. Bot Framework is the only one with an explicit batch `read`/`write` over multiple keys; aiogram and Rasa are single-key per call.
- **FSM vs. user data — three answers.** aiogram and Rasa cleanly separate routing state from data/history. PTB has **no FSM concept** — `bot_data`/`chat_data`/`user_data`/`conversations` sit at the same level. Bot Framework's `Storage` is undifferentiated key/blob; `ConversationState`/`UserState` is a naming convention on top, not a structural split.
- **Locking/CAS lives in the interface itself (Bot Framework's `e_tag`) or a sibling abstraction (Rasa's `LockStore`, aiogram's `BaseEventIsolation`) — never inside the Mongo-specific class.** Neither Mongo storage surveyed implements locking; `find_one_and_update()`/`upsert` give single-write atomicity, not a lock across a multi-step handler.
- **TTL is inconsistent, mostly a Redis feature.** Only `RedisStorage` (aiogram) exposes `state_ttl`/`data_ttl`. Neither Mongo storage configures a TTL index.
- **Serialization ownership varies.** aiogram/Rasa are JSON-first; PTB's core is pickle-first (`PicklePersistence`) — a real design choice, not an implementation detail, that forces JSON-only backends into a community shim.
- **Conformance suites exist only where a framework ships ≥3 backends internally.** aiogram's `TestStorages` and Rasa's `test_tracker_stores.py` each run one test body against every backend via `pytest.mark.parametrize`. PTB, Bolt, and Bot Framework's core do not — PTB tests each persistence class independently, and Bot Framework's community adapters carry no shared upstream suite.

## 4. MongoDB: common choice or outlier?

**First-party vs. third-party:** Rasa ships `MongoTrackerStore` first-party, no separate package. aiogram ships Mongo first-party too, but later than Memory/Redis, via community [PR #841](https://github.com/aiogram/aiogram/pull/841) (Feb 2022), not part of the original design. PTB has no first-party Mongo — only `ptbcontrib` or independent packages (`LucaSforza/MongoPersistence`). Bolt has no Mongo backend at all. Bot Framework's core SDK has none either — Mongo is a Bot Builder Community adapter, same status as Redis/DynamoDB there. Among the five frameworks, Mongo is first-party in exactly two (Rasa, aiogram), community/absent in the rest.

**Do these storages use Mongo's distinguishing features?** Not really. Neither `MongoTrackerStore` nor `PyMongoStorage`/`MongoStorage` configures a **TTL index** — expiry (where it exists at all) is Redis-only in this survey. Neither uses **change streams**. Both use atomic single-document writes (`find_one_and_update()`; `update_one(..., upsert=True)`), but that's ordinary document-atomicity, not a Mongo-specific advantage over a well-indexed SQL `UPDATE ... WHERE` or Redis. Rasa's cross-request locking is delegated entirely to `LockStore`, which has **no Mongo implementation** — even the framework leaning on Mongo hardest for data doesn't trust it for locking.

**PyMongo's async story is still settling.** `AsyncMongoClient` reached beta in PyMongo 4.9, GA in [4.13](https://pymongo.readthedocs.io/en/stable/changelog.html); MongoDB's docs state ["Motor will be deprecated on May 14th, 2026 ... migrate to the PyMongo Async API while Motor is still supported"](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/reference/migration/) (critical fixes until 2027-05-14). aiogram's own migration in [3.22.0](https://github.com/aiogram/aiogram/pull/1705) tracks this exactly — reacting to a driver deprecation, not choosing Mongo's async story as a settled foundation.

**Operational tradeoffs, as evidenced here:** Redis wins on TTL and locking primitives (backing `RedisEventIsolation` and `RedisLockStore`; Rasa's docs recommend it "for running a replicated set of Rasa servers"). SQL wins on transactional maturity and existing ops tooling, at the cost of schema/migration overhead. Mongo's evidenced advantage is schema flexibility for a heterogeneous data blob plus "the team already runs it" — not a TTL/change-stream/locking advantage these frameworks actually exploit.

**Verdict:** MongoDB for bot FSM/state reads as **defensible but not distinguished — usually "we already operate Mongo," not a decision made *because* of Mongo-specific durability or concurrency primitives.** Even Rasa, which leans on Mongo hardest for data, still routes locking through Redis/memory.

## 5. Framework vs. application ownership boundary

Where a clean split exists, it separates *routing/process state* from *domain data*: aiogram's `set_state`/`get_state` is "which handler branch am I admitted to," while `set_data`/`update_data` is an open `dict[str, Any]` the framework doesn't inspect. Rasa is sharpest: `TrackerStore` is domain-shaped dialogue history; `LockStore` is pure infrastructure the application never touches. PTB draws no line — everything is "whatever the application wants." Bolt draws no line because it has no state concept at all.

**Idempotency keys and dead-letter storage in the same store as FSM state: absent from all five frameworks surveyed.** No first-party or documented community-standard evidence of any framework here using its FSM/tracker/persistence store for idempotency keys or a DLQ. Rasa's `LockStore` only serializes processing order — it does not record "already handled" or hold failed events for replay. Where idempotency/DLQ patterns exist in these ecosystems, they live in application-level task-queue code (Celery/Taskiq-style retry/DLQ), not inside the bot framework's state store.

**A single "storage profile" backend driving state + locks + idempotency together: no precedent found.** Every framework that separates concerns (aiogram, Rasa) uses **two distinct abstractions** — never one object for both, and neither extends to idempotency/DLQ. aiommbot's plan for one storage profile serving all three does not match how any of these frameworks are built. That doesn't make it wrong, but it is a novel design choice to justify on its own merits, not one validated by precedent.

## 6. Recommendation for aiommbot

A minimal core `Protocol` should reuse verified pieces from aiogram's `BaseStorage` (the cleanest, most-tested contract surveyed) and Bot Framework's `Storage` (for the eTag/CAS idea), rather than invent new vocabulary:

```python
class StateStorage(Protocol):
    async def get_state(self, key: StorageKey) -> str | None: ...
    async def set_state(self, key: StorageKey, state: str | None) -> None: ...
    async def get_data(self, key: StorageKey) -> dict[str, Any]: ...
    async def set_data(self, key: StorageKey, data: dict[str, Any]) -> None: ...
    async def update_data(self, key: StorageKey, data: dict[str, Any]) -> dict[str, Any]: ...
    async def close(self) -> None: ...

class LockingStorage(Protocol):
    def lock(self, key: StorageKey) -> AsyncContextManager[None]: ...
```

`LockingStorage` stays a *separate* protocol — Rasa's `TrackerStore`/`LockStore` split and aiogram's storage/isolation split are both real, tested, in-production designs, unlike one profile serving state, locks, and idempotency at once (§5, no precedent found). TTL is extrapolated past a single framework's shape: only `RedisStorage` exposes it, so it should be optional backend configuration, not a required core method — forcing it in would make an in-memory/Mongo backend lie about a capability it lacks.

**First-party backends:** in-memory for tests/dev is universal. Redis is the strongest second candidate — the only backend implementing both TTL and a distributed lock, and Rasa recommends it for multi-replica deployments. Mongo/SQL should be optional extras: §4 shows Mongo support, even where first-party, arrived later than Memory/Redis, doesn't exploit TTL/change-streams, and (aiogram) is mid-migration off a deprecated driver. Given `CLAUDE.md`'s "small core, minimise runtime dependencies," Mongo belongs in an optional package, as Bot Framework treats Cosmos DB and Bolt treats SQLAlchemy.

**Conformance test suite:** aiogram's `TestStorages` and Rasa's `test_tracker_stores.py` both prove the pattern and are worth copying — one test body, parametrized across every backend fixture. aiommbot's core should ship an equivalent shared module (e.g. `aiommbot.testing.storage_conformance`) a third-party backend package can import and run against its own instance — the one place where precedent is unambiguous: PTB, Bolt, and Bot Framework's community adapters do none of this, and it shows in how unevenly those packages are tested.

## Sources

- aiogram: `aiogram/fsm/storage/base.py`, `fsm/storage/redis.py`, `fsm/storage/mongo.py`, `fsm/storage/pymongo.py`, `fsm/scene.py`, `CHANGES.rst`, `tests/test_fsm/storage/test_storages.py` (branch dev-3.x, https://github.com/aiogram/aiogram); Mongo storage origin https://github.com/aiogram/aiogram/pull/841 ("added mongo storage", 2022-02-18); Motor→PyMongo migration https://github.com/aiogram/aiogram/pull/1705 (3.22.0, 2025-08-17).
- python-telegram-bot: `src/telegram/ext/_basepersistence.py`, `_picklepersistence.py`, `_dictpersistence.py` (branch master, https://github.com/python-telegram-bot/python-telegram-bot); community Mongo persistence https://github.com/LucaSforza/MongoPersistence; `ptbcontrib` https://github.com/python-telegram-bot/ptbcontrib.
- Slack Bolt / slack_sdk: `slack_sdk/oauth/installation_store/installation_store.py`, `oauth/state_store/state_store.py`, `oauth/state_store/sqlite3/__init__.py` (https://github.com/slackapi/python-slack-sdk); Bolt's dependency on slack_sdk and lack of FSM confirmed in doc 03 (`slack_bolt/app/app.py`, `AGENTS.md`, https://github.com/slackapi/bolt-python); issue #380 (no test toolkit).
- Microsoft Bot Framework SDK: `libraries/botbuilder-core/botbuilder/core/storage.py`, `memory_storage.py`, `libraries/botbuilder-azure/botbuilder/azure/cosmosdb_partitioned_storage.py` (https://github.com/microsoft/botbuilder-python); community adapter https://github.com/sebsylvester/botbuilder-storage.
- Rasa: `rasa/core/tracker_store.py`, `rasa/core/lock_store.py`, `docs/docs/lock-stores.mdx`, `tests/core/test_tracker_stores.py` (https://github.com/RasaHQ/rasa); precursor community package https://github.com/m90/rasa-mongo-tracker-store.
- Botkit v4: `packages/docs/reference/core.md` (https://github.com/howdyai/botkit); community MS-storage adapter https://github.com/sebsylvester/botbuilder-storage.
- Botpress (best-effort): https://botpress.com/docs/adk-v2/conversations/state.
- discord.py: maintainer discussion https://github.com/Rapptz/discord.py/discussions/9180 ("Storing information permanently").
- aiogram-dialog: `src/aiogram_dialog/context/storage.py` (https://github.com/Tishka17/aiogram_dialog).
- MongoDB/PyMongo async status: https://www.mongodb.com/docs/languages/python/pymongo-driver/current/reference/migration/ (Motor deprecation 2026-05-14, critical fixes until 2027-05-14); PyMongo changelog https://pymongo.readthedocs.io/en/stable/changelog.html (AsyncMongoClient beta in 4.9, GA in 4.13).
