# Diagram conventions

_Status: reviewed (#35)._

All diagrams are **Mermaid** blocks inside Markdown. They render on GitHub and in the docs site,
are reviewed in pull requests and are diffed like code. No images, no binary diagram files.

## Levels (C4 model)

| Level | Used in | Mermaid syntax | Shows |
|---|---|---|---|
| System Context | `03-context-and-scope.md` | `C4Context` | the bot, its users, Mattermost, storage, operators |
| Container | `05-building-block-view.md` | `C4Container` | runnable units and stores in a deployment |
| Layers | `05-building-block-view.md` §5.3 | `C4Component` | the five layers of a process as boxes; arrows are the import direction |
| Component | `05-building-block-view.md`, each `components/*.md` | `C4Component` | the modules inside a container and their dependencies |
| Code | `components/*.md` when it helps | `classDiagram` | Protocols, key classes, generics |
| Deployment | `07-deployment-view.md` | `C4Deployment` | infrastructure nodes and which processes run on them |
| Dynamic | `06-runtime-view.md`, `components/*.md` | `sequenceDiagram` | one scenario end to end |
| State | `components/*.md` for stateful nodes | `stateDiagram-v2` | lifecycle and FSM states |

## Rules

- One diagram, one question. If a diagram needs a legend longer than three lines, split it.
- Names in diagrams are the `CONTEXT.md` terms, exactly.
- Every box on a Component diagram has a row in the inventory table directly under the diagram,
  and that row links to the box's document (Mermaid's C4 boxes carry no reliable link on GitHub).
  Every arrow is labelled with the verb and, for async paths, the mechanism (`await`, `queue`,
  `task`).
- Arrows are imports **on a Component or Layers diagram**: an arrow from A to B means A may import
  B, so every arrow points towards the Core and none leaves it. A diagram that contradicts the
  import-linter contracts is a bug in one of them.
- Arrows are traffic on a Context, Container or Deployment diagram, and the label names the
  protocol. A Deployment diagram nests `Deployment_Node` for infrastructure and puts a `Container`
  inside the node that runs it; it shows no module and repeats no import direction.
- Sequence diagrams show failure paths (`alt`/`else`) for the scenarios that motivate the design:
  reconnect, timeout, cancellation, storage unavailable.

## Renderer limits

- A `classDiagram` member containing `|` or `(…)` is parsed as a method; write `Optional~T~ name`
  and state optionality in the table instead.
- `Container_Boundary` does not render inside `C4Component`.
- C4 boxes carry no reliable hyperlink on GitHub; the inventory table holds the link.
- Mermaid carries a standing caveat on all five C4 diagram types — "This is an experimental diagram
  for now. The syntax and properties can change in future releases"
  ([mermaid.js.org/syntax/c4](https://mermaid.js.org/syntax/c4.html)) — so a C4 block stays inside
  the shapes already used in this catalogue and adopts no property a section does not need.

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
