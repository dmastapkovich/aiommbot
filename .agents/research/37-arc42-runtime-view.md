# 37. arc42 §6 as the template defines it and as public projects keep it

**Question.** What does arc42 itself require of a **runtime view (§6)** — how a scenario is
selected, how many are expected, whether a diagram is required and of what notation, whether *error
and exception* scenarios are asked for, what text accompanies a diagram — and where does the
template draw the line between §6 and §5, §8 and §9? Gathered for
[#39](https://github.com/dmastapkovich/aiommbot/issues/39), which writes the section and needs the
template's own rules before it invents any; its rulebook already asks a sequence diagram to show a
failure path ([`diagrams.md`](../../docs/design/diagrams.md)), so section 3 below is the
load-bearing half.

Sources are primary: the arc42 template in source form, the `docs.arc42.org` and `faq.arc42.org`
site sources, and published arc42 documents read as source in their repositories. Neither arc42 nor
Mermaid was in the local reference cache when this note was gathered, so every page here was fetched
over the network on 2026-09-11; both are rows of [`references.md`](../references.md) now, and the
next session reads them from `.refs/`. Where a negative is claimed, the whole
repository was downloaded as a tarball at `HEAD` and grepped in full, because GitHub's code-search
endpoint rejects unauthenticated requests with `401 Unauthorized` in this environment; an exhaustive
grep over the repository tree is the stronger check anyway.
[Note 28](28-arc42-deployment-view-and-cross-cutting-concepts.md) measured §7 and §8 across eleven
public documents and never touched §6; section 6 below is that table re-run for §6 over the same
eleven. Peer documents are evidence of practice, never authority. Anything a primary source did not
confirm is marked **[unverified]**.

## 1 §6 as the template defines it

The template file
[`EN/adoc/06_runtime_view.adoc`](https://github.com/arc42/arc42-template/blob/master/EN/adoc/06_runtime_view.adoc)
is 53 lines and 1,791 bytes. It defines the content as one sentence and four areas:

> The runtime view describes concrete behavior and interactions of the system's building blocks in
> form of scenarios from the following areas:
>
> * important use cases or features: how do building blocks execute them?
> * interactions at critical external interfaces: how do building blocks cooperate with users and
>   neighboring systems?
> * operation and administration: launch, start-up, stop
> * error and exception scenarios

**How a scenario is chosen, and how many.** One remark carries both, and it is the only selection
rule the template states:

> Remark: The main criterion for the choice of possible scenarios (sequences, workflows) is their
> *architectural relevance*. It is *not* important to describe a large number of scenarios. You
> should rather document a representative selection.

So the criterion is a property of the scenario (*architectural relevance*) and the quantity rule is
negative: not many, a representative selection. No number appears in the template.

**The motivation names an audience, and it is not the developers.**

> You should understand how (instances of) building blocks of your system perform their job and
> communicate at runtime. You will mainly capture scenarios in your documentation to communicate
> your architecture to stakeholders that are less willing or able to read and understand the static
> models (building block view, deployment view).

**Notation is a list of five options and an ellipsis.** The whole *Form* block:

> There are many notations for describing scenarios, e.g.
>
> * numbered list of steps (in natural language)
> * activity diagrams or flow charts
> * sequence diagrams
> * BPMN or EPCs (event process chains)
> * state machines
> * ...

Natural-language numbered steps come first in that list, and a diagram notation only third.

**The body is a bare heading per scenario, with two fill-in lines under the first.**
`=== <Runtime Scenario 1>` carries exactly two bullets:

```text
* _<insert runtime diagram or textual description of the scenario>_
* _<insert description of the notable aspects of the interactions between the
building block instances depicted in this diagram.>_
```

Then `<Runtime Scenario 2>`, `...` and `<Runtime Scenario n>` follow as empty headings.
[docs.arc42.org/section-6](https://docs.arc42.org/section-6/) numbers the same children 6.1, 6.2 …
6.n and renders the two bullets as two italic lines. That second line is the only place either
publication says what text goes beside a picture: a description of *the notable aspects of the
interactions between the building block instances*.

**§6 ships no named slots, no structure rule and no obligation.** §7 ships four named level-1 slots
(`Overview Diagram`, `Motivation`, `Quality and/or Performance Features`, `Mapping of Building
Blocks to Infrastructure`) and §8 ships a *Structure* block capping the number of entries; §6 ships
neither. Mechanically:

- `must` occurs zero times in `06_runtime_view.adoc` and zero times in the site page
  `_pages/section-6.md` — grepped for `\bmust\b` in both files.
- `mandatory` occurs exactly once in the whole English template and exactly once in the whole
  `_pages` and `_posts` content of
  [`arc42/docs.arc42.org-site`](https://github.com/arc42/docs.arc42.org-site), and it is the same
  sentence both times, in §5: "This view is mandatory for every architecture documentation."
  ([docs.arc42.org/section-5](https://docs.arc42.org/section-5/)). §6 is nowhere called mandatory.
- `.Structure` occurs in exactly one English chapter file, `08_concepts.adoc` — established by
  listing every `EN/adoc/*.adoc` file that matches `^\.Structure`. §6 has no such block, so it
  publishes no cap on the number of scenarios comparable to §8's "Pick **only** the most-needed
  topics for your system".
- §7 states when it is worth writing at all ("Especially document a deployment view if your
  software is executed as distributed system with more than one computer, processor, server or
  container …"). §6 publishes no equivalent trigger sentence — there is no "especially document a
  runtime view if …" anywhere in the template file or on the section page. The nearest statement is
  [FAQ B-4](https://faq.arc42.org/questions/B-4/), "What is the minimal amount of an arc42
  documentation?", which answers "There is no general rule" and then lists five aspects to "always
  explain, document or specify": quality requirements as scenarios, context view and external
  interfaces, solution strategy, building block view level 1, and "Most important crosscutting
  concepts". §6 is not in that list.

**The two publications differ in three words.** The AsciiDoc block is titled `.Contents`, the site
heading is `## Content`; the AsciiDoc says "architectural relevance", the site "architectural
relevancy"; the AsciiDoc says "neighboring systems", the site "neighbouring systems". The Markdown
publication shipped in the template's own `dist/` directory carries the help text verbatim from the
AsciiDoc — `arc42-template-EN-withhelp-gitHubMarkdown.zip` reproduces the four areas, the remark,
the motivation and the *Form* list word for word — while the per-chapter file of the multi-page
Markdown variant, `06_runtime_view.md`, is 413 bytes of headings and the two fill-in bullets with
no help text at all.

## 2 What the tips add that the template does not state

Eleven tips are published under `tips/6-*` — 6-1 through 6-11, no gaps, established by listing
[`_posts/06-runtime/`](https://github.com/arc42/docs.arc42.org-site/tree/main/_posts/06-runtime) —
and five FAQ questions under §6, `C-6-1` … `C-6-5`, established by listing
[`_posts/C-arc42/06-runtime/`](https://github.com/arc42/faq.arc42.org-site/tree/main/_posts/C-arc42/06-runtime).
Six things in them are not in the template.

**A number.** The template refuses to give one; [tip 6-2](https://docs.arc42.org/tips/6-2/),
"Document only a few runtime scenarios!", does: "In my (Gernot) experience, it's perfectly ok to
keep just 1-3 scenarios in your documentation - but use several dozens during design and development
of the system." It also splits the criterion in two. Scenarios to *create* are "the important ones,
that are _really_ specific, complex, risky or otherwise interesting" and "scenarios that help
_designing_ building blocks or challenge corresponding design decisions". Scenarios to *keep* are a
seven-item list: crucial to understanding the overall processing, critical for the top quality
goals, "especially risky in their implementation", involving "critical, volatile or unstable
external interfaces", "had been very difficult to implement", needing "special attention by some
stakeholders", "etc.".

**A mapping obligation.** `always` occurs in exactly one of the eleven tips, twice, and both times
in [tip 6-1](https://docs.arc42.org/tips/6-1/) — one of the two §6 tips tagged `essential`, the
other being tip 6-2. Its title: "Always map existing building blocks to the activities within
runtime scenarios!" Its body: "You should always use elements from your
[building block view](https://docs.arc42.org/section-5/) (or their runtime counterparts, like
instances of classes) within these scenarios." It then contrasts a scenario with
a *required function*, which "describe a required process or sequence of steps that the system
somehow needs to execute or perform (but regardless what element of the systems actually does it)",
and calls the bridge between them architecture work: "It's an important architecture task to map
from the latter (requirements) to the building blocks. In other words: You need to assign
responsibilities to your building blocks." [FAQ C-6-2](https://faq.arc42.org/questions/C-6-2/)
states the same as a block quote: "It's important that the runtime view shows **which building
block** is responsible for **what activities** or functions within the system."

**A level rule, and permission to mix levels.** [Tip 6-3](https://docs.arc42.org/tips/6-3/) asks for
"'schematic' (instead of detailed) scenarios": "In 'schematic' scenarios you refer to higher levels
of abstraction, to building blocks from higher levels (e.g. level-1) of the building block view."
[Tip 6-4](https://docs.arc42.org/tips/6-4/) permits the opposite and prices it — UML sequence
diagrams down to instances give "thoroughness and accuracy" at the cost of "immense creation and
maintenance effort, and the potentially low readability" — and its one bold instruction is "**Please
document details with caution - and only if relevant stakeholders really need them!**"
[Tip 6-10](https://docs.arc42.org/tips/6-10/) then sanctions mixing: "you can mix building blocks of
various abstraction levels (or sizes) in single scenarios, instead of showing all low-level
interactions", because "As you show some large or more abstract building blocks, you hide their
internal working or internal processes within the scenario."

**Partial scenarios, with a stated risk and a required countermeasure.**
[Tip 6-6](https://docs.arc42.org/tips/6-6/) opens "We have seen too many sequence diagrams
resembling the one below: Scenarios that just propagate date over several participants - usually
non-interesting stuff" and instructs: "Focus on risky, difficult, complicated or interesting parts",
"Don't hesitate to start right in the middle of a longer (overall) process", "Cut out boring,
standard, simple of straightforward stuff".
[FAQ C-6-4](https://faq.arc42.org/questions/C-6-4/) adds the risk and the fix: "A risk of partial
scenarios might be consumers that don't understand the prerequisites or preconditions of a partial
scenario. Use annotations within your diagrams to explicitly clarify such required knowledge or
facts." [FAQ D-7](https://faq.arc42.org/questions/D-7/) repeats the instruction as a rule about
diagram size: "Especially in runtime scenarios, don't always start with the beginning of a scenario,
but _dive-right-into_ the interesting parts."

**A named tool, in six of the eleven tips.** The template names no tool. PlantUML is named in
[tip 6-5](https://docs.arc42.org/tips/6-5/), [tip 6-6](https://docs.arc42.org/tips/6-6/),
[tip 6-7](https://docs.arc42.org/tips/6-7/), [tip 6-8](https://docs.arc42.org/tips/6-8/),
[tip 6-9](https://docs.arc42.org/tips/6-9/) and [tip 6-11](https://docs.arc42.org/tips/6-11/), and
each of the six prints one of its listings. Two of them argue from version control: "Such textual
descriptions can be merged and versioned like any other source code!" (6-5) and, in one of tip 6-9's
three bullets, "maintain the textual representations in common versioning tools (git, subversion
etc), with the established branching and merging options". Tip 6-11 argues from effort instead, not
from versioning — a textual DSL because "creating and managing sequence diagrams might take up a lot
of effort". Tip 6-5 also names what the syntax has to cover: "PlantUML supports most UML SD
constructs, like interaction references, loops, alternatives and so on." The FAQ names the same tool
in the same words: [F-10](https://faq.arc42.org/questions/F-10/) — the page
[C-6-3](https://faq.arc42.org/questions/C-6-3/) hands tool choice to — repeats "Such textual
descriptions can be merged and versioned like any other source code!" and adds DrawIO and
Web-Sequence-Diagrams beside it.

**Permission to throw the scenario away.** [Tip 6-5](https://docs.arc42.org/tips/6-5/) is titled
"Use scenarios primarily to `discover` building blocks, not so much for documentation!" and
[tip 6-9](https://docs.arc42.org/tips/6-9/) closes with the disposal rule: "in case such scenarios
are (later...) implemented in source code, the diagrams might be deleted, which will result in
leaner documentation". [FAQ H-3](https://faq.arc42.org/questions/H-3/), on keeping documentation in
step with code, ranks §6 last: "Prefer documenting \"crosscutting concepts\" (arc42 section 8) over
detailed building blocks (section 5) or runtime scenarios (section 6)."

## 3 Error and exception scenarios

**arc42 asks for them, in the template, in four words, as one of four content areas.** The fourth
bullet of the *Contents* block is "error and exception scenarios" — nothing more. That phrase
occurs **exactly once** in the whole `arc42/docs.arc42.org-site` repository tree (in
`_pages/section-6.md`), **exactly once** in the whole English template tree (in
`06_runtime_view.adoc`) and **zero times** in the whole `arc42/faq.arc42.org-site` tree.
Established by grepping all three downloaded tarballs at `HEAD` for `error and exception`.

**The FAQ restates it twice, and widens "error" to "failure".**
[FAQ C-6-2](https://faq.arc42.org/questions/C-6-2/), "What do I document or specify in the runtime
view?", lists four scenario types and the last is "The systems´ behavior in important error or
failure situations". [FAQ C-6-5](https://faq.arc42.org/questions/C-6-5/), "Which scenarios shall I
describe or document?", gives a nine-item candidate list of which three touch the same ground:
"Error or failure conditions that might influence overall system behavior.", "Interactions that
somehow deviate from _normal_ stakeholder expectation, especially deviate from developer
expectation." and "Interactions that work in non-standard ways." The qualifier in the first is
*influence overall system behavior* — the failure has to matter beyond its own call.

**No tip mentions error, exception or failure in prose.** Across all eleven `tips/6-*` pages the
word `error` occurs five times and every one of them is inside tip 6-9's PlantUML listing: a
participant declaration `participant "Error\nHandler" as EH`, two `else` labels (`else record
error`, `else file error`) and two messages (`IH -> EH: log record error`, `IH -> EH: log file
error`). The words `exception` and `failure` occur zero times in those eleven pages. Established by
grepping `_posts/06-runtime/` for `error`, `exception`, `failure` and `fail`. So no tip's prose
names a failure path, and the only one worked anywhere in the eleven tips sits unremarked inside a
code listing:

> ```
> alt parse file
> loop all records
> IH -> IH: parse record
> IH -> DM : store client
> else record error
> IH -> EH: log record error
> end
> else file error
> IH -> EH: log file error
> end
> ```
> ([tip 6-9](https://docs.arc42.org/tips/6-9/))

The tip's own prose never names what that `alt` block does; it is arguing for a textual DSL. Tip 6-8
draws a conditional the same silent way, `If "verbose?" then` … `else` … `Endif` inside its PlantUML
activity listing, and says nothing about it either. The one §6 *example* arc42 publishes that does
announce a failure path is MaMa, whose prose reads "The diagram below contains error handling"
(section 4), so the silence is a property of the tips, not of arc42's whole §6 material.

**Nothing anywhere obliges a scenario to carry an alternative or failure branch.** The word
`alternativ*` occurs twice in the eleven tips, both in
[tip 6-5](https://docs.arc42.org/tips/6-5/) and neither about a branch inside one scenario
("PlantUML supports most UML SD constructs, like interaction references, loops, alternatives and so
on"; "well-suited for discussing scenario alternatives among the development team"). `branch`
occurs once, about git. `happy path` occurs zero times. Established by grepping the eleven tips, the
section page, the five FAQ questions and the template file for `alternativ`, `branch` and `happy
path`. arc42's unit is the **scenario**: an error scenario is a scenario of its own, alongside the
use-case ones, not a branch appended to each.

**The nearest thing to a per-scenario obligation is about preconditions, not failures.**
[FAQ C-6-4](https://faq.arc42.org/questions/C-6-4/) attaches one duty to a partial scenario: "A risk
of partial scenarios might be consumers that don't understand the prerequisites or preconditions of
a partial scenario. Use annotations within your diagrams to explicitly clarify such required
knowledge or facts."

**The same subject is asked for in three other sections, in three different artefacts.**

- **§8 wants the rule.** [Tip 8-10](https://docs.arc42.org/tips/8-10/)'s checklist has an
  "Under-the-hood" row "Exception and error handling | What errors to handle, how to handle
  exceptional situations", and [FAQ C-8-2](https://faq.arc42.org/questions/C-8-2/)'s **Under the
  hood** group lists "exception and error handling" among its topics.
- **§10 and §1 want the measurable scenario.**
  [Tip 10-7](https://docs.arc42.org/tips/10-7/), "Consider fault/error/failure (quality)
  scenarios!!", says "Use quality scenarios to document or specify what kinds/categories of such
  failures or exceptions your system handles or has to handle", and its examples are stimulus and
  measured response: "The system recognizes within 60 seconds if an external payment provider
  becomes unavailable. It will then notify an administrator within 60 seconds."
  [FAQ C-10-2](https://faq.arc42.org/questions/C-10-2/) names "Failure scenarios: Some part of the
  system, its infrastructure or neighbors fail." as one of three quality-scenario kinds, and
  [tip 1-12](https://docs.arc42.org/tips/1-12/) calls the same kind "Failure or downtime scenarios:
  how does the system behave when a serious problem occurs, such as the failure of central hardware
  or software components."

So the three artefacts differ in kind, not in topic: §6 holds an **interaction** that fails, §8
holds the **rule** for handling failures across building blocks, §10 holds a **measurable
stimulus-response** pair. No arc42 page states that split explicitly — established by reading all
eleven `tips/6-*` pages, the section page, all five `C-6-*` questions, `tips/8-10`, `tips/10-7`,
`tips/1-12`, `C-8-2` and `C-10-2`, none of which contrasts the three.

## 4 Does §6 require a diagram, and of what kind

**No arc42 page states a diagram requirement for §6, and the template's own placeholder offers
prose instead.** The body line reads `_<insert runtime diagram or textual description of the
scenario>_` — the alternative sits inside the fill-in slot itself. `must` occurs nowhere in
[`06_runtime_view.adoc`](https://github.com/arc42/arc42-template/blob/master/EN/adoc/06_runtime_view.adoc)
or on [docs.arc42.org/section-6](https://docs.arc42.org/section-6/), established by grepping both
for `\bmust\b` with zero matches.

**The template offers five notation bullets closed by an ellipsis, and the natural-language one
comes first.** The bullets are quoted in section 1: numbered list of steps in natural language,
activity diagrams or flow charts, sequence diagrams, BPMN or EPCs, state machines, "...". Counting
distinct notations instead of bullets gives seven, because two of the five bullets name two each.
[FAQ B-2](https://faq.arc42.org/questions/B-2/), "Does arc42 prescribe or enforce specific
notations?", answers for the whole template: "No, arc42 works **completely** (!!) independent of
notation or syntax." [FAQ D-3](https://faq.arc42.org/questions/D-3/), "How do arc42 and UML relate
to each other?", is as permissive about the one notation it does discuss — "They don't really need
each other. You can very well use arc42 with and without UML." — and lists "runtime behavior or
runtime scenarios (runtime view)" as one of four aspects UML *might* describe.

**The FAQ ranks the options by cost, and puts plain text at the cheap end.**
[FAQ C-6-3](https://faq.arc42.org/questions/C-6-3/) says "The following list is ordered by
increasing documentation and maintenance effort" and gives three:

> 1. Document scenarios in plain text by enumerations or numbered lists. Include precise hints
>    which building block executes which step(s) of use cases, processes or functions.
> 2. Use activity diagrams or flowcharts with swim-lanes.
> 3. Use UML sequence diagrams. They can be time-consuming to create and maintain with most
>    interactive tools, but are an excellent means to show the mapping between building blocks and
>    their actions. See [question F-10 (tools for sequence diagrams)](/questions/F-10) for some tips
>    on tools.

That closing clause is where the FAQ hands tool choice on, and
[F-10](https://faq.arc42.org/questions/F-10/) is the one FAQ page that names tools: PlantUML, DrawIO
and Web-Sequence-Diagrams. C-6-3 itself closes by demoting the rest of UML: "UML has some additional
options (e.g. state transition or object diagrams) to describe behavioral aspects of systems or
building blocks. Those can be sometimes be useful, but are less often used that activity- or
sequence diagrams."

**Four tips teach a specific diagram form; three of them attach a price or a limit to it and the
fourth attaches nothing.** [Tip 6-11](https://docs.arc42.org/tips/6-11/) argues for UML sequence
diagrams — "They clearly denote the responsibility of all participating building blocks" — and then
prices them: "When using graphical modeling tools, creating and managing sequence diagrams might
take up a lot of effort. You could speed up that process by using a textual DSL (domain-specific
language) to describe the sequences and have somt tool render the diagrams for you."
[Tip 6-7](https://docs.arc42.org/tips/6-7/) teaches activity diagrams with swimlanes, defining one
by quotation — "A swimlane is a way to group activities performed by the same actor on an activity
diagram or to group activities in a single thread" — and records a tool limit rather than a cost:
"PlantUML (as of February 2017) can only render vertical swimlanes."
[Tip 6-1](https://docs.arc42.org/tips/6-1/) lists the three ways to satisfy the mapping obligation
and marks the price of the third: "Textual descriptions or numbered lists: There you have to
manually care for the mapping..." [Tip 6-8](https://docs.arc42.org/tips/6-8/) teaches activity
diagrams with *partitions* and names no cost at all: one sentence of introduction, an image, "The
diagram above was rendered by PlantUML with the following code:" and the listing.

**A table is never offered for §6.** The word `table` occurs zero times in a §6 sense across all
eleven `tips/6-*` pages, `_pages/section-6.md`, the five `C-6-*` questions and the template file —
the only matches are the substrings in "unstable" and "notable". Established by grepping those
eighteen files. This is the sharpest contrast with §7, where
[tip 7-7](https://docs.arc42.org/tips/7-7/) offers a table as an explicit alternative to a diagram
and [FAQ C-7-4](https://faq.arc42.org/questions/C-7-4/) asks for one beside it. For §6 the
sanctioned non-graphical form is a **numbered list of steps**, not a table.

**arc42 names no Mermaid and no C4 notation for §6.** The string `mermaid` occurs zero times in the
`_posts`, `_pages`, `_data` and `_examples` trees of `arc42/docs.arc42.org-site`, zero times in the
`_posts`, `_pages` and `_data` trees of `arc42/faq.arc42.org-site`, and zero times anywhere under
`EN/` in `arc42/arc42-template` — established by grepping the three downloaded trees. As note 28
found for §7, arc42 acknowledges C4 only in the FAQ and in its examples index, and the open template
issue [#228](https://github.com/arc42/arc42-template/issues/228), "Suggestion: Reference C4 Model as
an Diagramming Approach in arc42" (opened 2025-11-21, still open on 2026-09-11), is where the §6
mapping is proposed: its table's fourth row is "Runtime view (flow, sequence) | Dynamic | Direct
match".

**Mermaid has both notations, and the branch keywords §6's fourth content area needs.**
[mermaid.js.org/syntax/sequenceDiagram](https://mermaid.js.org/syntax/sequenceDiagram.html)
documents `alt`/`else` ("It is possible to express alternative paths in a sequence diagram"), `opt`
(a sequence "that is optional (if without else)"), `par` (actions "happening in parallel"),
`critical`/`option` (actions "that must happen automatically with conditional handling of
circumstances"), `break` ("It is possible to indicate a stop of the sequence within the flow
(usually used to model exceptions)"), `loop`, `rect`, notes spanning participants, activations, and
`autonumber` ("It is possible to get a sequence number attached to each arrow"). `C4Dynamic` is one
of the five C4 diagram types documented at
[mermaid.js.org/syntax/c4](https://mermaid.js.org/syntax/c4.html), with
`RelIndex(index, from, to, label, ?tags, $link)`, "Compatible with C4-PlantUML syntax, but ignores
the index parameter. The sequence number is determined by the order in which the rel statements are
written." The page carries the same standing caveat on all C4 support that note 28 quoted: "This is
an experimental diagram for now. The syntax and properties can change in future releases."

**arc42 publishes exactly three worked §6 examples, and they set the bar low.** The section page
ends with an examples gallery, `{% include example.md category="runtime" %}`, which resolves to the
three files matching `category: runtime` in
[`_examples/`](https://github.com/arc42/docs.arc42.org-site/tree/main/_examples) — HTML Sanity
Checker, MaMa and TPU. Two of the three open with the same editorial label, "A simple diagram with a
brief textual explanation."
([examples/runtime-1](https://docs.arc42.org/examples/runtime-1/),
[examples/runtime-tpu-1](https://docs.arc42.org/examples/runtime-tpu-1/)). The third,
[examples/runtime-mama-2](https://docs.arc42.org/examples/runtime-mama-2/), is the only §6 example
arc42 publishes whose prose announces an error path and marks it as the exception rather than the
rule: "The diagram below contains error handling. In _good cases_ there will be no errors. Calls to
`ImportErrorHandler` are only executed if errors occur!" It is also the only one that states a
precondition in the way [FAQ C-6-4](https://faq.arc42.org/questions/C-6-4/) asks for:
"**Prerequisite:** Data has been imported from external source, has been successfully filtered (i.e.
decrypted and decompressed)."

## 5 Where the template draws the §6 / §5 / §8 / §9 line

**The §5, §8 and §9 pages never name §6.** The word `runtime` occurs in exactly two of the twelve
`_pages/section-*.md` files of `arc42/docs.arc42.org-site`: `section-6.md` and `section-10.md`.
Nothing in `_pages`, `_posts`, `_examples`, `_data` or `_includes` links to `/section-6/` except the
section page's own `permalink:` and the row in `_data/sections.yml`. Established by grepping the
downloaded tree for `runtime` and for `section-6`. So the boundary is not drawn on the section
pages; it is drawn in four tips and two FAQ answers, and it runs in both directions.

**§6 → §5 is an obligation.** [Tip 6-1](https://docs.arc42.org/tips/6-1/) is the one §6 rule phrased
with *always*: "You should always use elements from your
[building block view](https://docs.arc42.org/section-5/) (or their runtime counterparts, like
instances of classes) within these scenarios." A scenario that introduces an element §5 does not
have is outside the rule.

**§5 → §6 is an option, and the two pointers §5 offers are different in kind.**
[Tip 5-9](https://docs.arc42.org/tips/5-9/), "Use runtime views to explain or specify whiteboxes!",
borrows the *technique* rather than the section: "In case you want to influence the internal
structure of a whitebox, but don't want to specify all details, you may apply techniques from the
runtime view: Describe the required (runtime) behavior of the whitebox, for example with:
pseudo-code / activity diagrams or flowcharts / state diagrams or state-machines. Such information
provides architects or developers with _some_ information _how_ this whitebox should be constructed
or build, but does not specify all contained details." So behaviour written to constrain **one**
building block's internals belongs in that block's white box, not in §6.
[Tip 5-23](https://docs.arc42.org/tips/5-23/), "Document or specify interfaces with runtime
scenarios!", sends the other way: "Some interfaces require several interactions between
participating building blocks (handshakes, business- or technical protocols). You can describe or
specify such interactions by runtime scenarios,
[arc42-section 7](https://docs.arc42.org/section-7/). You should reference such scenarios from the
documentation of the participating building blocks."
The section number and link in that sentence are wrong — runtime scenarios are §6, not §7 — and the
error is in the published source, `_posts/05-buildingblocks/2016-03-03-t-5-23.md` line 13. What the
tip does establish is the reference direction: the **building block** points at the scenario.
[§5's own template file](https://github.com/arc42/arc42-template/blob/master/EN/adoc/05_building_block_view.adoc)
also keeps an optional slot for behaviour in its black box description, "(Optional)
Quality-/Performance characteristics of the black box, e.g.availability, run time behavior, ....",
which is a property of one block rather than an interaction.

**§8 governs §6, not the reverse, and may quote a scenario.** Two statements, both primary:

- [FAQ C-8-1](https://faq.arc42.org/questions/C-8-1/) defines a crosscutting concept as "Decisions
  or rules that influence several:" and then lists, with no emphasis on any of them, "building
  blocks / parts of the implementation / runtime scenarios / interfaces / several developers". The
  third item is the load-bearing one here: a rule several scenarios obey is §8 material.
- §8's own *Form* block permits "cross-cutting model excerpts or scenarios using notations of the
  architecture views" ([docs.arc42.org/section-8](https://docs.arc42.org/section-8/)), so a scenario
  may sit inside a concept.

No arc42 page says the reverse — that a rule may be written inside a runtime scenario. The word
`scenario` occurs zero times across all eleven `tips/8-*` pages and zero times across all ten
`tips/9-*` pages; established by grepping `_posts/08-concepts/` and `_posts/09-decisions/`.
[FAQ H-3](https://faq.arc42.org/questions/H-3/) ranks the two for maintenance cost: "Prefer
documenting \"crosscutting concepts\" (arc42 section 8) over detailed building blocks (section 5) or
runtime scenarios (section 6)."

**§9 says nothing about behaviour, and its only rule that touches §6 is the anti-redundancy one.**
The words `behavi*`, `dynamic` and `scenario` occur zero times in `_pages/section-9.md` and zero
times in the template's `09_architecture_decisions.adoc` — grepped in both. §9's page carries
"**Avoid redundant texts.**"
([docs.arc42.org/section-9](https://docs.arc42.org/section-9/)), and
[tip 4-4](https://docs.arc42.org/tips/4-4/) gives the same instruction for §4 and points into §6 by
its correct number while doing so: "you should document only briefly - and refer (link) to detailed
explanations in arc42 sections 5 (building blocks), 6 (runtime view) or 8 (crosscutting concepts)."
Of the three tips outside `tips/6-*` that reach for the runtime view, it is the only one that gets
the number right: 5-23 sends the reader to runtime scenarios but calls them §7, and 5-9 borrows the
technique without naming a section. Whether a fourth such tip exists is **[unverified]** — the
`runtime` grep this run performed covers the twelve `_pages/section-*.md` files, not every file of
`_posts/`. So the sanctioned traffic is §4 → §6 and §5 → §6 for context, and §6 → §5 for the
elements it uses; a decision's rationale stays in §9.

**§10 keeps the measurable scenario, §6 the interaction.**
[docs.arc42.org/section-10](https://docs.arc42.org/section-10/) requires of its scenarios "Ensure
that your scenarios are specific and measurable" and defines a *usage scenario* as one that
"describe the system's runtime reaction to a certain stimulus … Example: The system reacts to a
user's request within one second." Nothing in §6 asks for a number. This is the same three-way split
section 3 established for failures, seen from the quality side.

**The operative distinction is grammatical, as it was for §7 and §8.** §5 holds what a building
block *is*, §6 holds what a set of them *does* in one named sequence, §8 holds a rule several of
those sequences obey, §9 holds why a choice was made. A statement about one block's internals is §5
whatever its topic ([tip 5-9](https://docs.arc42.org/tips/5-9/)); a rule that several scenarios obey
is §8 whatever its topic ([FAQ C-8-1](https://faq.arc42.org/questions/C-8-1/)). No arc42 page states
that four-way split in one place — established by reading all eleven `tips/6-*` pages, all five
`C-6-*` questions, the four section pages and the `tips/5-*`, `tips/8-*` and `tips/9-*` sets, none
of which contains it.

## 6 The published examples, measured

The eleven documents are those of [note 28](28-arc42-deployment-view-and-cross-cutting-concepts.md)
§5: the eight complete documents republished on [examples.arc42.org](https://examples.arc42.org/),
plus DokChess, Urbo and geOrchestra Gateway from arc42's own
[`in-the-wild.yml`](https://github.com/arc42/examples.arc42.org-site/blob/main/_data/in-the-wild.yml).
Byte counts for the first eight are the sizes of the hosted per-section Markdown files in
[`arc42/examples.arc42.org-site`](https://github.com/arc42/examples.arc42.org-site) at `HEAD`, read
2026-09-11; where an author's original is readable under `_systems/*/_originals/`, its own size is
given beside it. DokChess is the sum of its German per-subsection files, and HTML Sanity Checker and
geOrchestra Gateway are the size of the one §6 file in the project's own repository — all three read
from the GitHub file-listing API at `HEAD`. Urbo carries a `*` because its §6 is a byte range inside
one 80 KB `arc42.md`, which the file-listing API cannot size: that figure comes from a verbatim
transcription of the range and is approximate to within it.

Scenario counts are of headings that name a scenario, or — where a document lists its scenarios
without giving each a heading, as geOrchestra Gateway does — of the named items in that list. The
*Notation* and *Branch* columns read the published §6 together with the author's own diagram sources
where `_systems/*/_originals/` carries them, because a rendered raster picture answers neither
question; every such reading names the file it comes from.

| Document | §6 | Scenarios | Notation | Branch | Prose beside the diagram | Names its building blocks | Says why chosen | Cites a decision |
|---|---|---|---|---|---|---|---|---|
| [docToolchain v4](https://examples.arc42.org/systems/doctoolchain-v4/06-runtime-view/) | 3,339 B (7,803 B in the original) | 5 | PlantUML sequence diagrams in the AsciiDoc original, rendered PNGs on the hosted page | yes — `alt`/`else` in scenarios 2 and 5 | one bold-led paragraph after each picture ("Key differences from v3", "Recovery behaviour") | yes, by script and class name | yes, for two of the five | inline ids: `ADR-6` once, `ADR-8` twice, "Chapter 8.5" twice, `QS-10` once, `QS-17` twice |
| [biking2](https://examples.arc42.org/systems/biking/06-runtime-view/) | 424 B (395 B in the original) | 2 | two raster images, notation not named | no — "error handling … pretty basic and simple" | none: a heading and an image, no text | not in the text † | yes — "Two use cases stand out as worth an actual runtime view" | never |
| [MaMa](https://examples.arc42.org/systems/mama/06-runtime-view/) | 1,972 B | 1 use case in 2 phases | two raster images, notation not named | yes, stated in prose — "The diagram below contains error handling" | six numbered steps under the first image; a **Prerequisite:** paragraph before the second | yes — `ProcessControl`, `ImportErrorHandler`, `Client` | yes — "One of the major use cases is _Import File_" | never; links into §8 ("the filter concept") |
| [HTML Sanity Checker](https://examples.arc42.org/systems/htmlsc/06-runtime-view/) | 1,602 B hosted; 404 B in the project's own repository | 2 hosted, 0 in the repository | two raster PNGs, the second labelled "Sequence diagram" | no † | a numbered list under each image, the first labelled "**Explanation:**" | yes — `AllChecksRunner`, `PerRunResults`, `SinglePageResults`, `SingleCheckResults` | weakly — "A typical scenario within HtmlSC" | never; links into §8 ("section 8.2.1") |
| [Traffic Pursuit Unit](https://examples.arc42.org/systems/tpu/06-runtime-view/) | 2,155 B | 1, drawn four ways | UML sequence, communication, activity and extended activity diagrams, as raster exports | no † | a three-step key-steps list before the set, then one paragraph introducing each picture | yes — "The names of the building blocks are denoted below the activity names in curly braces" | no | never |
| [fin-mig](https://examples.arc42.org/systems/fin-mig/06-runtime-view/) | 860 B | 1, in three phases across two images | two raster images, generated as SVG by the hand-written `06-runtime.py` in `_originals/diagrams-src/`, whose header calls them "runtime sequence diagrams" | no † | one paragraph before the first image and three between the two, nothing after the second; no step list | yes — VSAM Reader, Segmentizer, Rule Processor, Packager, Target System Adapter | no | never |
| [status.arc42.org](https://examples.arc42.org/systems/status.arc42.org/06-runtime-view/) | 3,323 B hosted; 537 B in the original, the untouched arc42 placeholder | 4 | one raster sequence diagram for scenario 1 on the hosted page; scenarios 2–4 are numbered natural-language lists with no diagram; three PlantUML sources in `_originals/images/` | yes — `if (External Event occurs) then (yes)` / `else (no)` / `endif` in `_originals/images/06-system-startup.puml`, and in prose "A failing check is retried; a site is only marked `down` after 2 of 3 attempts, five seconds apart, fail" | numbered steps throughout, plus a measured paragraph explaining the concurrency scenario | yes — `domain`, `siteStats.GetSiteStatistics`, `repoStats.GetRepoStatistics`, `internal/probe` | only collectively, in the editors' opening note | never by id — "the architecture decisions that describe them", and zero `ADR` matches |
| [NFDI4Earth](https://examples.arc42.org/systems/nfdi4earth/06-runtime-view/) | 665 B | 0 | none | no | none | no | not applicable | points at §4, §5 and §7 instead |
| [DokChess](https://www.dokchess.de/06_laufzeitsicht/) | 2,564 B (`_index.md` 332 B + `01_zugermittlung.md` 2,232 B) | 1 | one raster sequence diagram, named as such in the prose | no † | a walkthrough of three paragraphs after the image | yes — XBoard-Protokoll-Subsystem, Engine, Spielregeln, Eröffnungsbibliothek | no; it calls the interaction "eine exemplarische Interaktion auf Subsystem-Ebene" | cites a **concept**, not a decision: "(→ 8.4 „Plausibilisierung und Validierung")" |
| [Urbo](https://gitlab.opencode.de/stadt-soest/city-app/soest-city-app/-/blob/main/docs/architecture/arc42.md) | ≈3,325 B `*` | 3 | Mermaid `sequenceDiagram` | no — zero `alt`/`else` | a numbered list before each diagram: five steps, five steps and four | yes, in bold — Citizen App, Spring Application, Keycloak, PostgreSQL, MeiliSearch, imgproxy | no | never — no `ADR` and no "decision" in the section |
| [geOrchestra Gateway](https://docs.georchestra.org/gateway/en/latest/arc42/runtime_view/) | 6,639 B | 3, plus a C4-coloured flowchart of the deployment context and two rendered Structurizr dynamic views | Mermaid `flowchart TD` in C4 colours and three Mermaid `sequenceDiagram` blocks, plus `structurizr-AuthenticationFlow.svg` and `structurizr-OAuthFlow.svg` embedded as images and generated from `/docs/structurizr/dynamic-views.dsl` | yes — `alt Authentication successful` / `else Authentication failed` | one introductory sentence before the flowchart, a bold title and nothing else before each sequence diagram, one clause per Structurizr view; the steps are numbered inside the diagrams | yes — Gateway, LDAP, OAuth2Provider, BackendService | no | there is no §9 in that document to cite |

`†` the diagrams are raster images that could not be read in this environment, and no diagram source
for them is published, so the answer comes from the section's prose alone; whether those pictures
contain a branch is **[unverified]**.
`*` Urbo's §6 is a byte range inside one file rather than a file of its own, so its size is measured
from a verbatim transcription of that range and is approximate; every other figure in the column is
a file size read from the GitHub file-listing API.

## 7 Observations the table makes mechanically

- **§6 is the short section.** Across the eight hosted documents it runs 424 B to 3,339 B, median
  1,787 B, and six of the eight are under 2.2 KB. Against the §7 and §8 sizes note 28 measured on
  the same eight files, §8 is the longer section in seven of eight — the exception is
  status.arc42.org, 3,323 B of §6 against 1,831 B of §8 — while §6 against §7 splits four–four.
- **The scenario count clusters exactly where tip 6-2 puts it.** The counts are 5, 2, 1, 2, 1, 1,
  4, 0, 1, 3, 3. Nine of eleven keep three or fewer, and eight of eleven fall inside
  [tip 6-2](https://docs.arc42.org/tips/6-2/)'s "just 1-3 scenarios". The two that exceed it are
  docToolchain v4 (5) and status.arc42.org (4).
- **No document encodes a scenario as a table row.** Zero of eleven. That matches the absence
  section 4 found on arc42's own pages, which never offer a table for §6 while offering one twice
  for §7.
- **Two of the *Form* block's five bullets are used by nobody, and one notation in use is not in the
  list.** BPMN, EPCs and state machines appear in none of the eleven. Eight of eleven name a
  sequence diagram (docToolchain v4, HSC, TPU, fin-mig, status.arc42.org, DokChess, Urbo,
  geOrchestra Gateway) — fin-mig only in its diagram script, `06-runtime.py`, which the hosted page
  never mentions; activity diagrams appear in TPU and in the PlantUML material status.arc42.org's
  editors worked from; five carry a numbered natural-language list as the scenario or beside it. TPU
  adds a UML *communication diagram*, which the *Form* list does not name.
- **A diagram is normal but not universal, and one document runs three scenarios without one.** Ten
  of eleven carry at least one diagram; NFDI4Earth carries none. status.arc42.org has one diagram
  for four scenarios, so both ends of arc42's effort-ordered list in
  [FAQ C-6-3](https://faq.arc42.org/questions/C-6-3/) occur inside a single published document.
- **Three documents draw a branch inside a scenario; one more states error behaviour in prose over
  a picture that cannot be read.** Read in the diagram sources, the branches are docToolchain v4's
  (`alt`/`else` in the PlantUML source of scenarios 2 and 5), geOrchestra Gateway's (`alt`/`else` in
  the LDAP flow) and status.arc42.org's (`if`/`else`/`endif` in `06-system-startup.puml`, which its
  hosted §6 states in prose as a retry rule); MaMa asserts a branch its raster picture hides, "The
  diagram below contains error handling"; and Urbo's three Mermaid diagrams contain zero
  `alt`/`else`. docToolchain v4 is the only one of the eleven with a scenario *dedicated* to
  failure — "Scenario 5: Error and Recovery — Publish Fails with HTTP 401 / Locked File" — and it
  declares that in its first line: "This scenario exercises the error-handling path, not the happy
  path."
- **Nine of eleven name the building blocks a scenario crosses; one has no prose at all and one has
  no scenario.** biking2's §6 is two headings and two images, and NFDI4Earth's has nothing to name.
  Every other document names its participants in the text, which satisfies tip 6-1's mapping
  obligation in prose rather than in the picture.
- **Three of eleven say why a scenario was chosen.** docToolchain v4 (for two of its five), biking2
  and MaMa. Five say nothing, HSC says it weakly ("A typical scenario within HtmlSC"),
  status.arc42.org says it only collectively in the editors' opening note, and NFDI4Earth has no
  scenario to justify.
- **Exactly one of eleven cites a decision record from §6, and the §6 → §8 pointer is four times
  as common.** docToolchain v4 references `ADR-6` once and `ADR-8` twice. Of the four documents note
  28 found keeping a numbered register — docToolchain v4, status.arc42.org, Urbo, DokChess — three
  never reference it from §6. DokChess points at a §8 *concept* instead, MaMa and HSC also link into
  §8, and docToolchain v4 points at "Chapter 8.5 Error Handling" twice beside its ADR ids, so this
  set carries four documents pointing §6 → §8 against one pointing §6 → §9.
- **Three of the eleven §6 sections were not written by the system's own team, or not written at
  all.** status.arc42.org's original §6 chapter is the unmodified arc42 placeholder — though the
  authors' `_originals/images/` carries three §6 PlantUML sources — and the hosted version opens
  "This chapter was still an empty template in the original documentation; the scenarios below are
  assembled from the sequence and activity diagrams and the architecture decisions that describe
  them"; NFDI4Earth's opens "Not written yet"; and HTML Sanity Checker's own repository carries a
  404-byte §6 whose entire body is "NOTE: Not appropriate for this system due to very simple
  implementation.", while the version republished on examples.arc42.org still shows two scenarios.
  The republished pair does not come from that file's recorded history: the GitHub commits API
  returns five commits for `src/docs/arc42/chapters/chap-06-Runtime.adoc`, and the blob at the
  oldest of them, `0dc3453` of 2021-10-17, already carries the NOTE and nothing else.
  **[unverified — where
  the examples editors took HSC's two scenarios from, since no commit on the current path holds
  them.]**
- **arc42's own list of published documents contains one that omits §6 outright.** The
  `in-the-wild.yml` file holds eight entries; their `sections:` tags are "All 12" five times, "All
  but 4 and 9" (geOrchestra Gateway), "Varies by team" (a university course) and "All but 6, 10 and
  11" (GA-Lotse). Established by listing every `- title:` and every `sections:` line in the file. So
  one of the eight documents arc42 links to has no runtime view at all.

## 8 What the evidence supports

- **§6 is defined by a selection rule, not by a structure.** The template gives four content areas,
  one selection criterion ("their *architectural relevance*"), a negative quantity rule ("It is
  *not* important to describe a large number of scenarios"), five notation bullets closed by an
  ellipsis, and two fill-in lines. It gives no named slots, no *Structure* block, no word of
  obligation, and no trigger sentence saying
  when the section is worth writing — where §7 has "Especially document a deployment view if …" and
  §5 is the one section arc42 calls "mandatory". [FAQ B-4](https://faq.arc42.org/questions/B-4/)'s
  minimal documentation set omits §6, and [FAQ B-1](https://faq.arc42.org/questions/B-1/) answers
  the general question with "Please don't _fill in everything_."
- **The number arc42 publishes is one to three, and it lives in a tip.**
  [Tip 6-2](https://docs.arc42.org/tips/6-2/): "it's perfectly ok to keep just 1-3 scenarios in your
  documentation - but use several dozens during design and development of the system." Eight of the
  eleven measured documents sit inside that range; the two that exceed it keep four and five.
- **The strongest rule about §6 is the mapping rule, and it is the only one phrased with *always*.**
  [Tip 6-1](https://docs.arc42.org/tips/6-1/), tagged `essential`: "You should always use elements
  from your building block view (or their runtime counterparts, like instances of classes) within
  these scenarios", restated by [FAQ C-6-2](https://faq.arc42.org/questions/C-6-2/) as "the runtime
  view shows **which building block** is responsible for **what activities**". Nine of the eleven
  documents satisfy it, and they satisfy it in prose — a numbered step list or a walkthrough naming
  the participants — not only inside the picture.
- **Error and exception scenarios are asked for once, in four words, and nowhere as a branch.** The
  phrase "error and exception scenarios" is the fourth content area and occurs exactly once in each
  of the template and the site; [C-6-2](https://faq.arc42.org/questions/C-6-2/) and
  [C-6-5](https://faq.arc42.org/questions/C-6-5/) restate it and widen "error" to "failure", with
  the qualifier that the condition "might influence overall system behavior". No tip prose mentions
  error, exception or failure, and the only failure path worked inside a tip is an unremarked `alt`
  block in [tip 6-9](https://docs.arc42.org/tips/6-9/)'s PlantUML listing; the one worked §6
  *example* that announces an error path is
  [MaMa](https://docs.arc42.org/examples/runtime-mama-2/), "The diagram below contains error
  handling." arc42's unit is the scenario, so in the template an error scenario is a scenario of its
  own, listed beside the use-case ones. In practice three of eleven documents draw a branch and one
  keeps a scenario dedicated to failure.
- **The same subject is asked for in three sections, in three different artefacts, and arc42 never
  contrasts them.** §6 wants the interaction that fails; §8 wants the rule ("Exception and error
  handling | What errors to handle, how to handle exceptional situations",
  [tip 8-10](https://docs.arc42.org/tips/8-10/)); §10 wants the measurable stimulus and response
  ([tip 10-7](https://docs.arc42.org/tips/10-7/),
  [FAQ C-10-2](https://faq.arc42.org/questions/C-10-2/)). Reading all three sets of pages produces
  no sentence that draws the line.
- **A diagram is not required, and the sanctioned non-graphical form is a numbered list of steps,
  never a table.** The fill-in slot itself says "runtime diagram **or** textual description";
  [FAQ C-6-3](https://faq.arc42.org/questions/C-6-3/) orders the options "by increasing
  documentation and maintenance effort" with plain text first;
  [FAQ B-2](https://faq.arc42.org/questions/B-2/) makes the whole template notation-independent; and
  `must` appears in neither publication of §6. A table is offered nowhere for §6 and by no measured
  document, which is the exact opposite of §7, where a table is offered twice. Ten of the eleven
  documents nevertheless draw something, and one (status.arc42.org) mixes a drawn scenario with
  three written ones inside the same section.
- **What text accompanies a diagram is stated once, and it is not a caption.** The template's second
  fill-in line asks for "description of the notable aspects of the interactions between the building
  block instances depicted in this diagram". In the measured set that takes two shapes — a numbered
  step list keyed to building blocks (HSC, MaMa, TPU, status.arc42.org, Urbo) or a paragraph of
  notable aspects after the picture (docToolchain v4, DokChess, and fin-mig after its first image
  only) — and exactly one document ships a diagram with no text at all.
- **Both Mermaid notations that could carry a §6 exist, and arc42 names neither.** `mermaid`
  occurs zero times across the template, the documentation site and the FAQ site.
  [Mermaid's sequence-diagram page](https://mermaid.js.org/syntax/sequenceDiagram.html) documents
  `alt`/`else`, `opt`, `par`, `critical`/`option`, `break` ("usually used to model exceptions"),
  `loop`, `rect`, notes, activations and `autonumber`; `C4Dynamic` with `RelIndex` is documented on
  [the C4 page](https://mermaid.js.org/syntax/c4.html) under the standing experimental caveat. Two
  of the eleven documents use Mermaid for §6 regardless, and the open template issue
  [#228](https://github.com/arc42/arc42-template/issues/228) proposes the row "Runtime view (flow,
  sequence) | Dynamic | Direct match". This repository's
  [`design/diagrams.md`](../../docs/design/diagrams.md) already maps its Dynamic row to `sequenceDiagram`
  and asks those diagrams to show failure paths with `alt`/`else`.
- **Saying why a scenario was chosen is the template's own criterion and is rare in practice.**
  Architectural relevance is the stated criterion and [tip 6-2](https://docs.arc42.org/tips/6-2/)
  expands it into a seven-item list of reasons to keep a scenario, yet only three of eleven
  documents write the reason down. The cheapest instance is biking2's single clause, "Two use cases
  stand out as worth an actual runtime view", inside a 424-byte section.
- **arc42 sanctions throwing the scenario away, and omitting the section is practised.**
  [Tip 6-5](https://docs.arc42.org/tips/6-5/) is titled "Use scenarios primarily to `discover`
  building blocks, not so much for documentation!";
  [tip 6-9](https://docs.arc42.org/tips/6-9/) says the diagrams "might be deleted" once the
  scenarios are implemented; [FAQ H-3](https://faq.arc42.org/questions/H-3/) ranks §8 above both §5
  and §6 for what to keep in sync with code. Consistent with that, HTML Sanity Checker's own
  repository has replaced its §6 with one NOTE, NFDI4Earth labels its §6 "Not written yet" and
  redirects to §4, §5 and §7, status.arc42.org left the arc42 placeholder untouched and the examples
  editors wrote the section for it, and GA-Lotse — in arc42's own list — is tagged "All but 6, 10
  and 11".
- **Where both a §6 and a decision register exist, the pointer §6 carries in practice runs to §8,
  not to §9 — four times as often.** One document of eleven cites an ADR from §6 (docToolchain v4,
  `ADR-6` once and `ADR-8` twice, each time attached to a statement of mechanism). Three others cite
  a §8 concept instead (DokChess's "(→ 8.4 …)", MaMa's filter concept, HSC's "section 8.2.1"), and
  docToolchain v4 points at "Chapter 8.5 Error Handling" twice beside its ADR ids. Three documents
  that keep a numbered register never reference it from §6. That is the mirror image of note 28's
  finding for
  §8, where the same pattern — name the record, state the mechanism, hand the detail back — appears
  as a §8 → §9 pointer.

## Sources

arc42 template, in source form:

- <https://github.com/arc42/arc42-template/blob/master/EN/adoc/06_runtime_view.adoc> · <https://github.com/arc42/arc42-template/blob/master/EN/adoc/05_building_block_view.adoc> · <https://github.com/arc42/arc42-template/blob/master/EN/adoc/09_architecture_decisions.adoc>
- <https://github.com/arc42/arc42-template> (repository tree at `master`, downloaded as a tarball at `HEAD` and grepped in full; the Markdown publications read from `dist/arc42-template-EN-withhelp-gitHubMarkdown.zip` and `dist/arc42-template-EN-withhelp-markdownMP.zip`)
- <https://github.com/arc42/arc42-template/issues/228>

arc42 documentation site (`docs.arc42.org`), pages, tips and worked examples:

- <https://docs.arc42.org/section-5/> · <https://docs.arc42.org/section-6/> · <https://docs.arc42.org/section-8/> · <https://docs.arc42.org/section-9/> · <https://docs.arc42.org/section-10/>
- <https://docs.arc42.org/tips/6-1/> · <https://docs.arc42.org/tips/6-2/> · <https://docs.arc42.org/tips/6-3/> · <https://docs.arc42.org/tips/6-4/> · <https://docs.arc42.org/tips/6-5/> · <https://docs.arc42.org/tips/6-6/> · <https://docs.arc42.org/tips/6-7/> · <https://docs.arc42.org/tips/6-8/> · <https://docs.arc42.org/tips/6-9/> · <https://docs.arc42.org/tips/6-10/> · <https://docs.arc42.org/tips/6-11/>
- <https://docs.arc42.org/tips/1-12/> · <https://docs.arc42.org/tips/4-4/> · <https://docs.arc42.org/tips/5-9/> · <https://docs.arc42.org/tips/5-23/> · <https://docs.arc42.org/tips/7-7/> · <https://docs.arc42.org/tips/8-10/> · <https://docs.arc42.org/tips/10-7/>
- <https://docs.arc42.org/examples/runtime-1/> · <https://docs.arc42.org/examples/runtime-mama-2/> · <https://docs.arc42.org/examples/runtime-tpu-1/>
- <https://github.com/arc42/docs.arc42.org-site> (site source; `_pages/`, `_posts/`, `_examples/`, `_data/`, `_includes/` — downloaded at `HEAD` on 2026-09-11 and grepped in full for every negative in sections 1 to 5)

arc42 FAQ (`faq.arc42.org`):

- <https://faq.arc42.org/questions/C-6-1/> · <https://faq.arc42.org/questions/C-6-2/> · <https://faq.arc42.org/questions/C-6-3/> · <https://faq.arc42.org/questions/C-6-4/> · <https://faq.arc42.org/questions/C-6-5/>
- <https://faq.arc42.org/questions/B-1/> · <https://faq.arc42.org/questions/B-2/> · <https://faq.arc42.org/questions/B-4/> · <https://faq.arc42.org/questions/C-8-1/> · <https://faq.arc42.org/questions/C-8-2/> · <https://faq.arc42.org/questions/C-10-2/> · <https://faq.arc42.org/questions/D-3/> · <https://faq.arc42.org/questions/D-7/> · <https://faq.arc42.org/questions/F-10/> · <https://faq.arc42.org/questions/H-3/>
- <https://github.com/arc42/faq.arc42.org-site> (site source; `_posts/C-arc42/06-runtime/` holds five questions, `C-6-1` … `C-6-5` — downloaded at `HEAD` and grepped in full)

Published arc42 documents:

- <https://examples.arc42.org/> · <https://github.com/arc42/examples.arc42.org-site> (per-system sources under `_systems/`, authors' originals under `_systems/*/_originals/` where present, external list in `_data/in-the-wild.yml`; downloaded at `HEAD` on 2026-09-11)
- <https://examples.arc42.org/systems/doctoolchain-v4/06-runtime-view/> · <https://github.com/arc42/examples.arc42.org-site/blob/main/_systems/doctoolchain-v4/_originals/chapters/06_runtime_view.adoc>
- <https://examples.arc42.org/systems/biking/06-runtime-view/> · <https://examples.arc42.org/systems/mama/06-runtime-view/> · <https://examples.arc42.org/systems/htmlsc/06-runtime-view/> · <https://examples.arc42.org/systems/tpu/06-runtime-view/> · <https://examples.arc42.org/systems/fin-mig/06-runtime-view/> · <https://github.com/arc42/examples.arc42.org-site/blob/main/_systems/fin-mig/_originals/diagrams-src/06-runtime.py>
- <https://examples.arc42.org/systems/status.arc42.org/06-runtime-view/> · <https://github.com/arc42/examples.arc42.org-site/blob/main/_systems/status.arc42.org/_originals/arc42/chapters/06_runtime_view.adoc> · <https://github.com/arc42/examples.arc42.org-site/blob/main/_systems/status.arc42.org/_originals/images/06-system-startup.puml>
- <https://examples.arc42.org/systems/nfdi4earth/06-runtime-view/>
- <https://github.com/aim42/htmlSanityCheck/blob/main/src/docs/arc42/chapters/chap-06-Runtime.adoc> (404 B; the project's current §6) · <https://api.github.com/repos/aim42/htmlSanityCheck/commits?path=src/docs/arc42/chapters/chap-06-Runtime.adoc> (five commits, oldest `0dc3453` of 2021-10-17)
- <https://www.dokchess.de/06_laufzeitsicht/> · <https://github.com/DokChess/website_de/tree/master/content/06_laufzeitsicht>
- <https://gitlab.opencode.de/stadt-soest/city-app/soest-city-app/-/blob/main/docs/architecture/arc42.md> (Urbo — Smart City Platform)
- <https://docs.georchestra.org/gateway/en/latest/arc42/> · <https://docs.georchestra.org/gateway/en/latest/arc42/runtime_view/> · <https://github.com/georchestra/georchestra-gateway/blob/main/docs/arc42/runtime_view.md> (6,639 B; the document's §6 in source form)
- <https://gitlab.opencode.de/ga-lotse/ga-lotse-documentation> (GA-Lotse, the entry tagged "All but 6, 10 and 11"; its §6 absence is taken from arc42's own list, not from the document)

Diagram notation:

- <https://mermaid.js.org/syntax/sequenceDiagram.html> · <https://mermaid.js.org/syntax/c4.html>

Searches that returned nothing, and how they were run. GitHub's code-search endpoint answers
`401 Unauthorized` without a token in this environment, so each arc42 repository was downloaded as a
tarball at `HEAD` and grepped in full, which is exhaustive where code search is not:

- `\bmust\b` over `EN/adoc/06_runtime_view.adoc` and `_pages/section-6.md` — zero matches.
- `mandatory` over the whole `EN/` tree of `arc42/arc42-template` and over `_pages/` and `_posts/`
  of `arc42/docs.arc42.org-site` — one match each, the same §5 sentence.
- `^\.Structure` over every `EN/adoc/*.adoc` file — one file, `08_concepts.adoc`.
- `error`, `exception`, `failure`, `fail` over all eleven files of `_posts/06-runtime/` — five
  matches, all inside tip 6-9's PlantUML listing; zero for `exception` and `failure`.
- `error and exception` over the whole `arc42/docs.arc42.org-site` tree, the whole
  `arc42/faq.arc42.org-site` tree and the whole `EN/` tree of the template — one, zero and one.
- `alternativ`, `branch`, `happy path` over the eleven tips, `_pages/section-6.md`, the five
  `C-6-*` questions and the template file — two matches for `alternativ` (both tip 6-5, neither
  about a branch in one scenario), one for `branch` (about git), zero for `happy path`.
- `table` over the same eighteen files — zero §6-sense matches; the hits are the substrings inside
  "unstable" and "notable".
- `mermaid` over `_posts/`, `_pages/`, `_data/` and `_examples/` of `arc42/docs.arc42.org-site`,
  over `_posts/`, `_pages/` and `_data/` of `arc42/faq.arc42.org-site`, and over the whole `EN/`
  tree of the template — zero matches in all three.
- `runtime` over the twelve `_pages/section-*.md` files — matches in `section-6.md` and
  `section-10.md` only.
- `section-6` over `_pages/`, `_posts/`, `_examples/`, `_data/` and `_includes/` of
  `arc42/docs.arc42.org-site` — two matches, the section page's own `permalink:` and the row in
  `_data/sections.yml`.
- `scenario` over all eleven `_posts/08-concepts/` pages and all `_posts/09-decisions/` pages —
  zero matches.
- `behavi`, `dynamic`, `scenario` over `_pages/section-9.md` and the template's
  `09_architecture_decisions.adoc` — zero matches.

One limit of this run, stated because it shaped the method: the authenticated GitHub CLI stopped
working part-way through the session (its configuration file became unreadable in this sandbox), so
the four arc42 repositories were downloaded as tarballs before that point and grepped locally, while
the documents held outside those repositories — HTML Sanity Checker's §6, DokChess's two §6 files,
Urbo's §6 range and geOrchestra Gateway's §6 — were read afterwards as raw files over the network.
What the CLI's loss cost is narrower than it looks: the unauthenticated GitHub file-listing and
commits APIs both answer, so HSC's, DokChess's and geOrchestra Gateway's §6 sizes are exact file
sizes and HSC's file history is readable (five commits, the oldest already carrying only the NOTE).
Only Urbo's figure stays approximate, and for a reason particular to it: its §6 is a byte range
inside one 80 KB file, the file-listing API sizes whole files rather than ranges, and the range
itself was read as text rather than as raw bytes, so the figure is measured from a verbatim
transcription and marked `*` in the table. Two things remain unread: the raster diagrams of five
documents, marked `†`, and the provenance of the two scenarios the examples editors published for
HSC, marked **[unverified]** in section 7.
