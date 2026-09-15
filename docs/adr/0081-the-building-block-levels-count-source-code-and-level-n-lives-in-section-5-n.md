---
status: accepted
date: 2026-09-15
ticket: "#109"
---

# The building block levels count source code, level-0 is §3, and level-n is documented in section 5-n

arc42 fixes the counting and we were one out of step with it at every heading: "Level-n of the
building block view shall be documented in section 5-n of the building block view, where level-0
(zero) is the context view and level-1 your topmost system whitebox" (FAQ C-5-11), no level is
skipped (tip 5-12), and what the hierarchy refines is the **source code** (tip 5-2, `essential`).
[§5](../design/05-building-block-view.md) called the one-box system level 1, the containers level 2
and the components level 3. We adopted arc42's counting:

- **Level 0 is [§3](../design/03-context-and-scope.md), level 1 is the five layers, level 2 is the
  components of each layer.** The layer model of
  [ADR-0032](0032-layer-model-and-direction-of-allowed-dependencies.md) is the topmost whitebox
  because §5 refines source code, and no layer, rank or component moves: this decision renames
  levels and renumbers sections, nothing else.
- **A process is not a level.** What a deployment runs are processes, and no arc42 page in the 320
  searched relates a building block level to a process or a deployment unit; the one page on C4 (FAQ
  B-17) maps nothing. The process-shape view stays in §5 because it names the same blocks — a
  container is a plugin list over one `Bot` object — and it carries no level and no number.
- **Level-n lives in section 5-n.** 5.1 is the level-1 whitebox: the layer diagram, the reason the
  cut is there, and a blackbox row per layer. 5.2 holds the level-2 whiteboxes as 5.2.1 through
  5.2.5, one per layer, in import-rank order.
- **The seams are the level-1 whitebox's interfaces, at 5.1.1.** That is the template's own
  `<Name interface m>` slot under 5.1 and the shape the published `tpu` document uses for its
  `Important Interfaces`. The seam inventory of
  [ADR-0038](0038-seam-inventory-records-the-direction-of-the-call.md) is unchanged — thirteen rows,
  sixteen Protocols, twelve required and one provided.
- **Every whitebox says why its decomposition is that one**, in a paragraph after the diagram and
  before the inventory table — the template's own order, and where 8 of the 12 rationale paragraphs
  in the published documents sit. Tip 5-8 asks for it in *every* whitebox; 13 of 27 published
  whiteboxes carry one, and the Core and the Adapter now do.

## Considered options

- *Keep the section numbers and record the departure the way §10 records its own* — rejected: it
  buys a smaller commit with a permanent footnote, and arc42 sanctions no non-level §5 subsection
  anywhere in the 320 pages searched, so the departure would have been ours to defend at every
  reading rather than once.
- *Drop the level words from the headings and name the views instead* — the practice of 4 of the 8
  published documents, which number nothing and so never contradict C-5-11. Rejected: it discards
  the vocabulary the template and the two measured sections are written in, and a hierarchy with no
  names for its levels cannot state that no level is skipped.
- *Move the process-shape view to [§7](../design/07-deployment-view.md)* — rejected: §7.2 says what
  a host must promise a process, and the view here says which plugin list makes one. The two are
  different questions about the same three processes.
- *Put the seams inside the Core's whitebox as 5.2.1.x* — rejected: they are the framework's
  substitution points rather than the Core's internal parts, and the level-1 whitebox is where a
  reader looks for what an application plugs into.

## Consequences

- The catalogue holds sixty-five references of the form `§5.x`; sixty of them point at this section
  and all sixty were rewritten, with twelve anchors, across twenty files in the commit that made
  this decision. The other five point at the §5 of `components/event.md` and of
  [`docs/research/22`](../research/22-public-import-surface-of-modern-libraries.md) and are
  untouched. The window was this one: thirty-two `LLD: <component>` documents cite §5 and none of
  them is written yet.
- **A level is not a layer.** Five layers are one level, and the glossary now carries
  *Building block level* so the two words cannot be swapped.
- Two sections of §5 carry no number — the reading guide and the inventory summary. arc42 sanctions
  neither: it is silent across the 320 pages searched, and 0 of the 8 published documents measured
  adds a reading guide or a summary inventory to §5. They are this catalogue's, kept because §5 is
  the inventory behind thirty-two tickets and a reader needs to be told how to count it.
