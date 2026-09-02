# Diagram conventions

_Status: reviewed (documentation foundation)._

All diagrams are **Mermaid** blocks inside Markdown. They render on GitHub and in the docs site,
are reviewed in pull requests and are diffed like code. No images, no binary diagram files.

## Levels (C4 model)

| Level | Used in | Mermaid syntax | Shows |
|---|---|---|---|
| System Context | `03-context-and-scope.md` | `C4Context` | the bot, its users, Mattermost, storage, operators |
| Container | `05-building-block-view.md` | `C4Container` | runnable units and stores in a deployment |
| Component | `05-building-block-view.md`, each `components/*.md` | `C4Component` | the modules inside a container and their dependencies |
| Code | `components/*.md` when it helps | `classDiagram` | Protocols, key classes, generics |
| Dynamic | `06-runtime-view.md`, `components/*.md` | `sequenceDiagram` | one scenario end to end |
| State | `components/*.md` for stateful nodes | `stateDiagram-v2` | lifecycle and FSM states |

## Rules

- One diagram, one question. If a diagram needs a legend longer than three lines, split it.
- Names in diagrams are the `CONTEXT.md` terms, exactly.
- Every box on a Component diagram links to a component document; every arrow is labelled with
  the verb and, for async paths, the mechanism (`await`, `queue`, `task`).
- Dependencies point in the direction imports are allowed to point. A diagram that contradicts the
  import-linter contracts is a bug in one of them.
- Sequence diagrams show failure paths (`alt`/`else`) for the scenarios that motivate the design:
  reconnect, timeout, cancellation, storage unavailable.

## Example

```mermaid
C4Context
    title System context — a bot built on aiommbot
    Person(user, "Mattermost user", "Talks to the bot in channels and DMs")
    System(bot, "Bot process", "Built on aiommbot 0.5.0")
    System_Ext(mm, "Mattermost server", "WebSocket events, REST API, interactive callbacks")
    SystemDb_Ext(store, "State store", "Optional: Redis or other backend")
    Rel(user, mm, "posts, clicks buttons")
    Rel(mm, bot, "events over WebSocket; callbacks over HTTPS")
    Rel(bot, mm, "REST API calls")
    Rel(bot, store, "conversation state, locks")
```
