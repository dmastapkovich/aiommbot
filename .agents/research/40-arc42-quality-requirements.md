# 40. arc42 §10 (Quality requirements) as the template defines it and as public projects keep it

**Question.** What does arc42 require of §10 (Quality requirements) — in the template's own words,
in its tips and in its FAQ — and how do published arc42 documents keep it? In particular: what is
the exact grammar of a quality scenario, how many scenarios does arc42 publish for, and **may a
test, a check or a tool gate serve as the measure** where a number cannot?

Gathered for [#108](https://github.com/dmastapkovich/aiommbot/issues/108), serving
[#37](https://github.com/dmastapkovich/aiommbot/issues/37), which writes §1, §2 and §10 of this
project's architecture document. This note is the §10 half of a split pair;
[`39-arc42-goals-and-constraints.md`](39-arc42-goals-and-constraints.md) carries §1 and §2, and its
finding 4 settles the §1.2 ↔ §10 division of labour that this note assumes. Section numbering
continues from that note, so the findings here start at **11**.

**Source policy.** Four arc42 repositories were read at their default-branch HEAD on
**2026-09-14**: the template (`arc42/arc42-template`), the documentation site (docs.arc42.org), the
FAQ site (faq.arc42.org) and the examples site (examples.arc42.org). Everything from those four is
quoted from the source of the published page and cited by its canonical URL. The network was used
only for `quality.arc42.org` and for the three published documents arc42 links to but does not host
(DokChess, Urbo, geOrchestra Gateway). Peer documents are evidence of practice, never authority.
Anything a primary source did not confirm is marked **[unverified]**.

**How a negative was established.** Every "arc42 never says X" names the trees grepped and the
pattern. "The §10 material" means all four of: the template's chapter file
`EN/adoc/10_quality_requirements.adoc`, `docs.arc42.org-site/_pages/section-10.md`, all eight tip
files in `docs.arc42.org-site/_posts/10-quality/`, and all five FAQ files in
`faq.arc42.org-site/_posts/C-arc42/10-quality/` — read in full, not sampled.

**One source-hygiene note.** The `examples.arc42.org` repository carries agent-facing files at its
root — a `CLAUDE.md` opening "Instructions for agents working in this repository" with prose-style
rules, plus `AGENTS.md`, `CONTRIBUTING.md` and `DESIGN.md` — and its `_data/in-the-wild.yml` opens
with roughly 90 lines of maintainer directives in comment form. Those are that project's
instructions to its own maintainers and contributors. They were read as data only; none was
followed, and no claim below rests on them.

---

## 11 What the template publishes as §10's children

The chapter file
[`EN/adoc/10_quality_requirements.adoc`](https://github.com/arc42/arc42-template/blob/master/EN/adoc/10_quality_requirements.adoc)
opens §10 with:

> **.Content** This section contains all relevant quality requirements.
>
> The most important of these requirements have already been described in section 1.2. (quality
> goals), therefore they should only be referenced here. In this section 10 you should also capture
> quality requirements with lesser importance, which will not create high risks when they are not
> fully achieved (but might be _nice-to-have_).
>
> **.Motivation** Since quality requirements will have a lot of influence on architectural
> decisions you should know what qualities are really important for your stakeholders, in a
> specific and measurable way.
>
> **.Further Information**
>
> * See https://docs.arc42.org/section-10/[Quality Requirements] in the arc42 documentation.
> * See the extensive https://quality.arc42.org[Q42 quality model on https://quality.arc42.org].

Two children follow.

**`=== Quality Requirements Overview`** — note the heading. It is **not** called "Quality Tree" in
the current template.

> **.Content** An overview or summary of quality requirements.
>
> **.Motivation** Often we encounter dozens (or even hundreds) of detailed quality requirements. In
> this overview section you should try to summarize, e.g. by describing categories or topics (as
> suggested by [ISO 25010:2023] or [Q42]).
>
> **If these summary descriptions are already precise, specific enough and measurable, you may skip
> section 10.2.**
>
> **.Form** Use a simple table in which each line contains a category or topic and a short
> description of the quality requirement. Alternatively, you may use a mindmap to structure these
> quality requirements.
>
> In literature, the idea of a _quality attribute tree_ has also been described, which puts the
> generic term "quality" as the root and uses a tree-like refinement of the term "quality".
> [Bass+21] introduced the term "Quality Attribute Utility Tree" for this purpose.

**`=== Quality Scenarios`**

> **.Content** Quality scenarios make quality requirements concrete and allow to decide whether
> they are fulfilled (in the sense of acceptance criteria). **Ensure that your scenarios are
> specific and measurable.**

followed by the two scenario kinds (section 13) and the two scenario forms (section 12), an
`.Examples` block pointing at quality.arc42.org, and a `.Further Information` block citing "Len
Bass, Paul Clements, Rick Kazman: 'Software Architecture in Practice', 4th Edition, Addison-Wesley,
2021."

### 11.1 The fill-in lines, and what actually ships

The AsciiDoc template ships **no fill-in line at all** for either child — the help blocks are the
entire file. [docs.arc42.org/section-10/](https://docs.arc42.org/section-10/) adds two:

- `_<Give an overview of quality requirements here >_`
- `_<describe quality scenarios here >_`

Extracting `arc42-template-EN-plain-markdownStrict.zip` from
[`dist/`](https://github.com/arc42/arc42-template/tree/master/dist) shows what a user receives:
`# Quality Requirements`, then `## Quality Requirements Overview` and `## Quality Scenarios` as bare
headings with nothing beneath either, then `# Risks and Technical Debts`. **No table, no columns, no
placeholder row.** Compare §1.3, which is the only place in §1/§2/§10 where the template ships a
real table skeleton.

### 11.2 The tips are stale relative to the template

[Tip 10-1](https://docs.arc42.org/tips/10-1/) still describes §10's children as "the quality tree
(section 10.1)" and "the quality scenarios (section 10.2)". The template's 10.1 is titled *Quality
Requirements Overview*, and the tree appears in it only as a literature reference. An author
following the tips alone would build a section arc42's own template no longer asks for. This
mismatch recurs in section 15 below.

---

## 12 The exact grammar of a scenario — arc42 publishes two forms, and neither is "stimulus → response → measure"

The template's §10.2 `.Form` block publishes **two** named, attributed forms.

**The short form, "favoured in the Q42 model" — three parts:**

> * **Context/Background**: What kind of system or component, what is the envirionment or
>   situation?
> * **Source/Stimulus**: Who or what initiates or triggers a behaviour, reaction or action.
> * **Metric/Acceptance Criteria**: A response including a _measure_ or _metric_

**The long form, "favoured by the SEI and [Bass+21]" — eight fields:**

> * **Scenario ID**: A unique identifier for the scenario.
> * **Scenario Name**: A short, descriptive name for the scenario.
> * **Source**: The entity (user, system, or event) that initiates the scenario.
> * **Stimulus**: The triggering event or condition the system must address.
> * **Environment**: The operational context or condition under which the system experiences the
>   stimulus.
> * **Artifact**: The building-blocks or other elements of the system affected by the stimulus.
> * **Response**: The outcome or behavior the system exhibits in reaction to the stimulus.
> * **Response Measure**: The criteria or metric by which the system's response is evaluated.

Both blocks are identical in the template chapter and on
[docs.arc42.org/section-10/](https://docs.arc42.org/section-10/). The long form is the SEI/ATAM
six-part scenario (source, stimulus, environment, artifact, response, response measure) with an ID
and a name prepended — arc42 attributes it to the SEI and to Bass, Clements and Kazman rather than
claiming it.

**The FAQ publishes a third, four-part decomposition.**
[Question C-10-2](https://faq.arc42.org/questions/C-10-2/), under a schematic figure:

> * Event/stimulus: Any condition or event arriving at the system
> * System (or part of the system) is stimulated by the event.
> * Response: The activity undertaken after the arrival of the stimulus.
> * Metric (response measure): The response should be measurable in some fashion.

and [question C-10-3](https://faq.arc42.org/questions/C-10-3/) compresses it into a sentence: "A
quality scenario describes a concrete, measurable situation: a stimulus arriving at the system
under specific conditions, and the expected response or behavior."

### 12.1 Verdict on the project's own checklist

This project's quality checklist currently says **"stimulus → response → measure"**. Measured
against the sources:

- **It is not the template's phrasing.** Grepped the whole of `arc42-template/EN`,
  `docs.arc42.org-site/_pages`, `docs.arc42.org-site/_posts` and `faq.arc42.org-site/_posts` for
  `stimulus`: **15 hits** — six in the template's chapter 10, the same six repeated on
  `section-10.md`, two in question C-10-2 and one in question C-10-3. All are quoted in the three
  blocks above. No arc42 page anywhere publishes a three-term "stimulus, response, measure" triple.
- **It is closest to FAQ C-10-2**, which is four terms, not three, and names the *system* as the
  second term.
- **It drops the one part both of the template's forms make first-class: the context.** The Q42
  short form leads with "Context/Background"; the SEI long form carries "Environment" and
  "Artifact". A three-term compression loses the situation in which the stimulus arrives, which is
  what makes a scenario decidable rather than a slogan.
- **It is SEI vocabulary in origin**, not arc42's own, and arc42 says so explicitly by attributing
  the long form "to the SEI and [Bass+21]".

**The minimal form arc42 itself sanctions is therefore three parts but a different three:**
Context → Source/Stimulus → Metric/Acceptance Criteria. That is the one arc42 marks as its own
house style ("favoured in the Q42 model") and the cheaper of the two.

---

## 13 Scenario kinds and quantity

### 13.1 Kinds: the template names two, everything else names three

**The template and the section page name two:**

> Two kinds of scenarios are especially useful:
>
> * _Usage scenarios_ (also called application scenarios or use case scenarios) describe the
>   system's runtime reaction to a certain stimulus. This also includes scenarios that describe the
>   system's efficiency or performance. Example: The system reacts to a user's request within one
>   second.
> * _Change scenarios_ describe the desired effect of a modification or extension of the system or
>   of its immediate environment. Example: Additional functionality is implemented or requirements
>   for a quality attribute change, and the effort or duration of the change is measured.

**Everything else names three**, adding failure:

| Source | Kinds named |
|---|---|
| Template §10.2 / [docs.arc42.org/section-10/](https://docs.arc42.org/section-10/) | usage, change — **two** |
| [Tip 10-5](https://docs.arc42.org/tips/10-5/) / [10-6](https://docs.arc42.org/tips/10-6/) / [10-7](https://docs.arc42.org/tips/10-7/) | usage, change, "fault/error/failure" — three, one tip each |
| [Tip 1-12](https://docs.arc42.org/tips/1-12/) | "Usage scenarios / Change scenarios / **Failure or downtime scenarios**" |
| [Question C-10-2](https://faq.arc42.org/questions/C-10-2/) | "1. Usage scenarios / 2. Change (or modification) scenarios / 3. **Failure scenarios**: Some part of the system, its infrastructure or neighbors fail." |

So the template is the outlier: it omits the failure kind that three other arc42 pages publish. An
author should treat **usage / change / failure** as arc42's list, since two of its three
publications carry all three and only the template's `.Content` block is short.

Each kind gets worked examples arc42 publishes itself — [tip
10-5](https://docs.arc42.org/tips/10-5/) ("Administrators can modify access rights of users via GUI
with a maximum of five clicks"), [tip 10-6](https://docs.arc42.org/tips/10-6/) ("Integration of a
new (external) payment provider is possible within a maximum of two person-weeks"), [tip
10-7](https://docs.arc42.org/tips/10-7/) ("The system recognizes within 60 seconds if an external
payment provider becomes unavailable").

### 13.2 Quantity: arc42 publishes no bound for §10, and one explicit licence to write none

Grepped the §10 material for every number bounding §10.2's scenario count. **There is no upper
bound and no lower bound.** What arc42 publishes instead is an expectation of *many*:

| Source | Statement |
|---|---|
| Template §10.1 `.Motivation` | "Often we encounter dozens (or even hundreds) of detailed quality requirements." |
| [Tip 10-1](https://docs.arc42.org/tips/10-1/) | "We participated in the development of several systems having **more than 100 different quality scenarios**. In such cases, arc42 section 10.2 is the right place to document these (if they are not contained within written and easily accessible requirements documentation)." |
| [Question C-1-7](https://faq.arc42.org/questions/C-1-7/) | "In real-world systems we often find **>100 different quality scenarios**, way too many to digest _all-at-once_." |
| [Question C-10-5](https://faq.arc42.org/questions/C-10-5/) | same sentence, repeated |

And one sentence permitting **zero** — the only quantity rule arc42 publishes for §10, in the
template's §10.1 `.Motivation`:

> **If these summary descriptions are already precise, specific enough and measurable, you may skip
> section 10.2.**

The "top 3-5" everywhere in the corpus belongs to §1.2 and never to §10; see
[`39-arc42-goals-and-constraints.md`](39-arc42-goals-and-constraints.md) finding 2 for the nine
places it appears.

**Net for #37.** §10.2's count is unbounded above and may legitimately be empty *provided* §10.1's
overview is itself precise, specific and measurable. That last clause is the whole condition, and
it is the one most published documents ignore (section 18).

---

## 14 What may serve as the measure — the load-bearing question

**Answer: the measure need not be a number. arc42 requires that fulfilment be *decidable*, and it
publishes, as its own examples, measures that are a test suite, a conformance criterion across
named targets, and an invariant.**

### 14.1 What arc42 actually demands

Every normative sentence in the corpus. Grepped the §10 material plus the template's chapter 1 for
`measurab|measure|metric`:

| Source | Sentence, verbatim |
|---|---|
| Template §10.2 `.Content` | "Quality scenarios make quality requirements concrete and **allow to decide whether they are fulfilled (in the sense of acceptance criteria)**. Ensure that your scenarios are specific and measurable." |
| Template §10 `.Motivation` | "you should know what qualities are really important for your stakeholders, in a specific and measurable way." |
| Template §10.1 `.Motivation` | "If these summary descriptions are already precise, specific enough and measurable, you may skip section 10.2." |
| Template §10.2 `.Form`, Q42 short form | "**Metric/Acceptance Criteria**: A response including a _measure_ or _metric_" |
| Template §10.2 `.Form`, SEI long form | "**Response Measure**: **The criteria** or metric by which the system's response is evaluated." |
| [Question C-10-2](https://faq.arc42.org/questions/C-10-2/) | "Metric (response measure): The response should be measurable **in some fashion**." |
| [Question C-10-3](https://faq.arc42.org/questions/C-10-3/) | "These scenarios make quality requirements **testable and verifiable** — they are what drives architectural decisions, not the categories or tags above them." |

Three of these do the licensing work. The SEI field is "**the criteria** or metric" — criteria, not
only metrics. The FAQ says "measurable **in some fashion**". And C-10-3 restates the whole goal as
*testable and verifiable*, which a passing conformance suite satisfies exactly.

**No arc42 sentence anywhere requires a number.** Grepped the §10 material for
`number|numeric|quantif|threshold`: zero matches in any normative sentence.

### 14.2 arc42's own published examples where the measure is a test, a check or an invariant

These are not peer documents; they are examples arc42 publishes on its own site under its own
authorship, and they are the strongest evidence available.

| arc42 page | Example, verbatim | Measure kind |
|---|---|---|
| [examples/quality-requirements-1/](https://docs.arc42.org/examples/quality-requirements-1/) (§1.2, HtmlSC) | "2 \| Correctness \| **Correctness of every checker is automatically tested for positive AND negative cases.**" | a test suite |
| [examples/quality-requirements-1/](https://docs.arc42.org/examples/quality-requirements-1/) | "1 \| Correctness \| Every broken internal link (cross reference) **is found**." | conformance, no number |
| [examples/quality-requirements-1/](https://docs.arc42.org/examples/quality-requirements-1/) | "1 \| Safety \| Content of the files to be checked is _never_ altered." | an invariant |
| [examples/quality-htmlsc-2/](https://docs.arc42.org/examples/quality-htmlsc-2/) (§10.2, HtmlSC) | "10.2.3 \| **Correctness of all checks is ensured by automated positive and negative tests.**" | a test suite, in §10.2 itself |
| [examples/quality-htmlsc-2/](https://docs.arc42.org/examples/quality-htmlsc-2/) | "10.2.4 \| The results-report must contain _all_ results (aka findings)" | completeness criterion |
| [Tip 10-6](https://docs.arc42.org/tips/10-6/) | "The system must be usable with the database systems DB2, Oracle and MySQL **without source code modifications**." | conformance across named targets |
| [Tip 10-7](https://docs.arc42.org/tips/10-7/) | "In case of non-treatable application- or runtime exceptions the system will create appropriate logging events, that allow to diagnose the error, but **do not contain personal user or account data** (of data security category 2 or higher)." | a content invariant |
| [Question C-10-4](https://faq.arc42.org/questions/C-10-4/) | "When storage devices fail, the system **gracefully shuts down** (instead of crashing uncontrollably)." | behavioural criterion, no number |

### 14.3 arc42 also names the measuring rig

[Tip 1-15](https://docs.arc42.org/tips/1-15/) quotes a Q42 entry in full, and it is the closest
arc42 comes to a model answer for a library with no production telemetry:

> **Requirement.** All automated unit tests for a subsystem must execute quickly enough to give
> developers rapid feedback.
>
> **Acceptance criteria**
>
> * All unit tests for a subsystem complete in less than 180 seconds
> * **Test execution time is measured on standard CI/CD infrastructure**

Two things to take from it. The *thing measured* is the test suite — arc42 treats the project's own
build as a legitimate subject of a quality scenario. And the criterion names **where** it is
measured, because a duration without a rig is not decidable. Where a project substitutes a gate for
a duration, the equivalent obligation is to name the gate: *which* suite, *which* rule, *which*
command.

### 14.4 What arc42 does not license

The boundary is not numbers-versus-tests; it is decidable-versus-not.

- Template §10.2: scenarios must "allow to decide whether they are fulfilled". A criterion nobody
  can evaluate fails this regardless of how it is phrased.
- Template §1.2 `.Motivation`: "Make sure to be very concrete about these qualities, **avoid
  buzzwords**."
- [Tip 1-15](https://docs.arc42.org/tips/1-15/): "Asking stakeholders 'what are your quality
  requirements?' usually produces silence, or buzzwords."

So "the system is maintainable" is out; "the conformance suite passes" and "the lint rule holds"
are in — provided the suite and the rule are named, so that a reader can run them. **[unverified]**
in one respect only: no arc42 page uses the words *tool gate*, *conformance suite* or *linter*.
The licence is inferred from arc42's own published examples (14.2) and from its "criteria",
"in some fashion" and "testable and verifiable" phrasings (14.1), not from a sentence that names
the case.

---

## 15 The quality tree — deprecated as a graphic, optional as a structure, never required

### 15.1 Is it required at all? No

The template's 10.1 is titled **Quality Requirements Overview**, and its `.Form` publishes a table
first, a mindmap second, and the tree only as a literature note:

> Use a simple table in which each line contains a category or topic and a short description of the
> quality requirement. Alternatively, you may use a mindmap to structure these quality
> requirements.
>
> In literature, the idea of a _quality attribute tree_ has also been described […] [Bass+21]
> introduced the term "Quality Attribute Utility Tree" for this purpose.

The word "tree" does not appear in the template's heading, its `.Content` or its `.Motivation` —
only in that closing paragraph, describing what *literature* does.

### 15.2 arc42 deprecated the graphical tree, in writing

[Tip 10-2](https://docs.arc42.org/tips/10-2/) is titled "Document and explain the specific quality
tree! **(deprecated!)**" and opens with the retraction:

> In previous versions of this tip, we proposed a graphical quality tree. Now, a few years later,
> **we favor a simple table instead of the graphics.**
>
> A discussion of our reasons lies beyond the scope of this documentation. In short: Our own
> pragmatical quality model [Q42] makes use of **tags/labels instead of a strict hierarchy**. That
> proved to be a major improvement over the graphics.

and closes with the condition under which the tree still earns its place: "Such a tree _can_
provide a good overview of required qualities, it can document focus points. **If it grows larger,
all overview gets lost - and a simple table will win.**"

[Question C-10-3](https://faq.arc42.org/questions/C-10-3/) gives the reasoning at length, under the
headings "The classic approach: Quality Trees", "The modern approach: Tagging and labelling with
Q42" and "What really matters: Quality Scenarios":

> While quality trees provide a visual overview, they have practical limitations: The strict
> hierarchy forces quality properties into a single branch, even though many properties (e.g.
> "response time") could belong to multiple categories. Maintaining such trees becomes cumbersome
> as the number of quality requirements grows.

> Regardless of whether you use a classic quality tree or the modern Q42 tagging approach, the
> **detailed quality scenarios are the most important part** of your quality requirements. […]
> **Focus your effort on writing precise, specific quality scenarios rather than debating the
> perfect hierarchy or tagging scheme.**

### 15.3 Notations arc42 publishes, in its own order of preference

1. **A simple table** — one row per category or topic plus a short description (template §10.1
   `.Form`; [tip 10-2](https://docs.arc42.org/tips/10-2/) "we favor a simple table").
2. **A mindmap** — "Alternatively, you may use a mindmap" (template §10.1 `.Form`); [tip
   10-3](https://docs.arc42.org/tips/10-3/), "Mind-maps provide the ability to hierarchically
   structure (like a tree), but are sometimes more reader-friendly. […] We like to include
   references to specific scenarios in the tree."
3. **Q42 tags/labels** — "#flexible, #efficient, #usable, #operable, #testable, #secure, #safe" and
   #reliable" ([docs.arc42.org/section-10/](https://docs.arc42.org/section-10/)).
4. **A graphical tree** — deprecated ([tip 10-2](https://docs.arc42.org/tips/10-2/)).

### 15.4 Depth: arc42 publishes none

Grepped the §10 material for `\b(level|depth|deep|two levels|three levels)\b`: **two matches, both
incidental** — tip 10-5's "top-level goals" and tip 10-6's "service-level agreements". No arc42
sentence prescribes how deep a tree should go.

What the FAQ describes structurally is a shape, not a depth:
[question C-10-3](https://faq.arc42.org/questions/C-10-3/) — "The root 'quality' is hierarchically
refined into _areas_ or topics, which themselves are refined again. **Quality scenarios form the
leaves of such a tree.**" The one arc42 figure that can be counted, the ISO 25010:2023 tree in [tip
10-4](https://docs.arc42.org/tips/10-4/), is two levels (characteristic → sub-characteristic)
before the scenarios attach as leaves.

### 15.5 The relation to ISO 25010

Yes, and arc42 states it as generic-versus-specific.

- [Question C-10-3](https://faq.arc42.org/questions/C-10-3/): "Standards for product quality, like
  ISO 25010, propose _generic_ quality trees. […] The quality of a specific system can be described
  by a _specific_ quality tree."
- Template §10.1 `.Motivation`: "you should try to summarize, e.g. by describing categories or
  topics (**as suggested by** ISO 25010:2023 or Q42)."
- [Tip 10-4](https://docs.arc42.org/tips/10-4/) turns it into a five-step gap-finding procedure:
  "1. Start with something similar to the ISO 25010:2023 quality tree. 2. Let your stakeholders
  create quality scenarios 3. Attach those scenarios to a specific quality tree 4. **In case some
  of the major branches of your tree have no scenarios, that might be an indicator for missing
  scenarios.** […] 5. Let your stakeholders decide wether these topics are not relevant or if the
  corresponding scenarios are just missing or have been forgotten."

Step 4 is the only genuine *use* arc42 publishes for the tree: as a checklist that makes an absence
visible. Every other justification it once had has been withdrawn.

---

## 16 §10's relations to §6, §8, §1 and §11

### 16.1 §6 and §8: confirmed negative, from §10's side

An earlier note in this catalogue established from the §6 side that §6 holds the interaction, §8
the rule and §10 the measurable stimulus-response, and that no arc42 page draws the line
explicitly. **Measured from §10's side, that is confirmed.**

Grepped the §10 material — template chapter 10, `_pages/section-10.md`, all 8 tips in
`_posts/10-quality/`, all 5 files in `faq .../C-arc42/10-quality/` — for
`section.?(6|8|11)|runtime view|crosscutting|building.block|risk`. Six hits:

- two are the SEI long-form field "**Artifact**: The building-blocks or other elements of the
  system affected by the stimulus" (template and section page — the same block twice);
- two are §10's own `.Content` sentence "which will not create high **risk**s when they are not
  fully achieved";
- two are tip 10-8's table columns.

**Zero hits name section 6, section 8, the runtime view or crosscutting concepts.** arc42 draws no
line between them from this side either.

### 16.2 What §10's own pages add to the question

Two things the §6-side note could not see.

**The SEI "Artifact" field is arc42's only mechanism for binding a scenario to a building block.**
"**Artifact**: The building-blocks or other elements of the system affected by the stimulus"
(template §10.2 `.Form`). arc42's own long form therefore expects a scenario to *name the element
it bears on* — but the relation runs §10 → element, never §10 → §6. It is a field of the scenario,
not a cross-reference to a section.

**The one cross-section relation arc42 does publish for §10 is to §4, not to §6 or §8.**
[Tip 10-8](https://docs.arc42.org/tips/10-8/), "Use (quality) scenarios for architecture analysis
or evaluation!", publishes a four-column table "similar to the structure proposed in tip 4-2
(solution approach as table)":

| **Quality goal** | **Scenario** | **Solution approach** | **Risk** |
|---|---|---|---|
| _<Q-goal 1>_ | _<Text>_ | _<Text>_ | _<risk-1>_ |

So where arc42 asks what a scenario *connects to*, the answer it publishes is the solution approach
(§4) and the risk — both carried **inside** §10's own table rather than by pointers outward.

### 16.3 §10 → §1

Dense and explicit — the full evidence is in
[`39-arc42-goals-and-constraints.md`](39-arc42-goals-and-constraints.md) finding 4. In one line:
the template's rule is that §1.2's goals "should only be referenced here", while [tip
10-2](https://docs.arc42.org/tips/10-2/) says §10 should "Show your most important quality goals
and -requirements". Where they disagree the template governs: **§10 references §1.2, it does not
restate it.**

[Question C-10-5](https://faq.arc42.org/questions/C-10-5/) explains why §10 sits near the end of
the document at all: "arc42 suggests to document or specify the top 3-5 quality requirements in
section 1.2 - right at the start of the documentation. That's helpful, as some of these
requirements might influence the most important, fundamental (or often expensive...) architecture
decisions." The high-priority few go first; §10 holds the multitude.

### 16.4 §10 → §11

**No pointer exists.** The word "risk" appears in §10's material twice, and neither instance
references section 11: once in §10's own `.Content` ("quality requirements with lesser importance,
which will not create high risks when they are not fully achieved"), and once as the **Risk** column
of [tip 10-8](https://docs.arc42.org/tips/10-8/)'s evaluation table — which puts the risk *inside*
§10 rather than sending it to §11. Grepped as in 16.1; those are the only two.

---

## 17 The measured half — §10 across eleven published documents

The same eleven documents two earlier notes in this catalogue used: the eight complete documents
republished on [examples.arc42.org](https://examples.arc42.org), plus DokChess (German), Urbo and
geOrchestra Gateway, which arc42 links to but does not host. §1 and §2 are measured over the same
eleven in [`39-arc42-goals-and-constraints.md`](39-arc42-goals-and-constraints.md) section 17,
which also carries the provenance caveat and the reason `rgcat` is excluded.

Three of the eight hosted §10 files are **editorial notes by the examples.arc42.org maintainers
reporting that the original document has no §10** — not short sections, absent ones. They are
marked *(editorial note)* and counted as zero.

### 17.1 §10 — Quality requirements

| Document | §10 bytes | Sub-sections | Quality tree? | Scenarios | Scenario form | Measure: number / gate / prose | §1.2 duplicated? | ISO or Q42 named? |
|---|---|---|---|---|---|---|---|---|
| [docToolchain v4](https://examples.arc42.org/systems/doctoolchain-v4/10-quality-requirements/) | 8 222 | `Quality Requirements Overview`, `Quality Scenarios` (+2 sub-groups) | yes — **mindmap image**, ISO 25010 categories, 2 levels, leaves tagged `[goal N]` / `[derived]` | **19** (QS-1…QS-19) | **full SEI eight-column table**: `ID \| Goal \| Source \| Stimulus \| Artifact \| Environment \| Response \| Response Measure` | **14 gate** · 7 number · 0 pure prose | **no — pointer**, "Each leaf is annotated as either concretising one of the five Chapter 1.2 top quality goals (`[goal N]`) or as a `[derived]` quality requirement … this is correct arc42, not a defect." | **ISO 25010** |
| [biking2](https://examples.arc42.org/systems/biking/10-quality-requirements/) | **909** | `Quality Tree`, `Evaluation Scenarios` | yes — **image only**, no text | **2** | free prose under bold pseudo-headings | 1 number+gate · 1 prose | no mention of §1.2's five goals at all | no |
| [MaMa-CRM](https://examples.arc42.org/systems/mama/10-quality-requirements/) | 2 067 | `Flexibility Scenarios`, `Runtime Performance Scenarios`, `Security Scenarios` — **no 10.1/10.2 split** | **none** — redirected to §1.2.2 | **11** (F1-F6, P1-P2, S1-S3) | table `Id \| Scenario`, one free-text column | **9 number** · 1 gate · 1 prose | **no — pointer**, "(for a brief overview of quality requirements, please see section 1.2.2)" | no |
| [HTML Sanity Checker](https://examples.arc42.org/systems/htmlsc/10-quality-requirements/) | 1 251 | `Quality Scenarios` only | **none, and says why** — "For our small example, such a quality tree is overly extensive… in real-live systems we've seen quality trees with more than 100 scenarios." | **7** | table `Attribute \| Description` | 1 number · 1 **gate** · 5 prose | pointer, via the retained template blockquote | no |
| [Traffic Pursuit Unit](https://examples.arc42.org/systems/tpu/10-quality-requirements/) | 2 719 | `10.1 Quality Tree`, `10.2 Quality Scenarios` — the only doc matching the template's old numbering exactly | yes — **as a table**, `Quality Category \| Quality \| Description \| Scenario`, 13 rows over 7 categories, 2 levels | **4** (SC1-SC4) | table `Id \| Scenario`, one free-text column | 1 number · 1 gate · 2 prose | **yes — restated**, with a note admitting it: "the (1), (2), (3) in the following table repeat the top level quality requirements from chapter 1.2" | no |
| [fin-mig (M&M)](https://examples.arc42.org/systems/fin-mig/10-quality-requirements/) | **520** *(editorial note)* | none | none | **0** | — | — | pointer to §1.2 and §9 | no |
| [status.arc42.org](https://examples.arc42.org/systems/status.arc42.org/10-quality-requirements/) | **537** *(editorial note)* | none | none | **0** | — | — | pointer to §1; claims §1.2's goals *already are* scenarios "with a concrete threshold" | no |
| [NFDI4Earth](https://examples.arc42.org/systems/nfdi4earth/10-quality-requirements/) | **671** *(editorial note)* | none | none | **0** | — | — | pointer to §1; explains the omission — the goals are "kept as goals rather than pinned down as measurable scenarios" | **ISO 25010:2011** |
| DokChess | see 17.2 | — | — | — | — | — | — | — |
| Urbo | see 17.2 | — | — | — | — | — | — | — |
| geOrchestra Gateway | see 17.2 | — | — | — | — | — | — | — |

**Footnotes to the hosted eight.**

1. *Measure kinds.* A scenario is counted as **number** when its criterion names a quantity (a
   duration, a percentage, a count, a threshold), as **gate** when it names a test, a check, a
   command, an exit code, a byte-comparison, a named test rig or an external conformance standard,
   and as **prose** when no criterion permits a decision. A scenario carrying both is counted in
   both columns, so a row's three figures may sum to more than its scenario count. Every one of the
   43 scenarios in the five documents that have any was classified by hand from its own text, not
   from a summary: `doctoolchain-v4`'s 19 Response Measures were extracted and read individually,
   which is why its figures here differ from a first pass over the same file.
2. *`biking2`'s quality tree is an image with no textual equivalent* (`10-quality-tree.png`), so its
   depth and content could not be read from the source and are not reported. The original repository
   also holds `10_quality_tree.nm5`, a mind-map file, which was not opened.
3. *`doctoolchain-v4`'s tree is likewise a PNG*; its structure is reported from the alt text
   and from the prose that introduces it, not from the image.
4. *The three editorial notes* (`fin-mig`, `status.arc42.org`, `nfdi4earth`) are statements by the
   examples.arc42.org maintainers about the originals, not text by the original authors. For
   `nfdi4earth` the claim is independently sourced — the note cites the consortium's own online
   version as well as the PDF.

### 17.2 The three documents arc42 links to but does not host

These three are not on examples.arc42.org, so they were fetched over the network on 2026-09-14. Two
fetch passes were run independently and reconciled; where they disagreed, the raw source file
settled it, and the disagreements are recorded in the footnotes rather than hidden.

| Document | §10 size | Sub-sections | Quality tree? | Scenarios | Scenario form | Measure: number / gate / prose | §1.2 duplicated? | ISO or Q42 named? |
|---|---|---|---|---|---|---|---|---|
| [DokChess](https://www.dokchess.de/10_qualitaetsanforderungen/) (German) | 3 878 B over two sub-pages | `10.1 Qualitätsbaum`, `10.2 Qualitätsszenarien` | yes — an **opaque PNG**, introduced as "in Form eines sogenannten Qualitätsbaumes (englisch: Utility Tree)"; the §1.2 goals are drawn into the image and point at the scenario ids. Depth not readable from source | **15** — W01-05, K01, F01-04, E01-02, Z01-02, P01, the first letter naming the quality characteristic | table `ID \| Szenario`, one prose sentence per cell | **5 number** · 6 gate · 4 prose | **no — pointer, and bidirectional**: "Die Qualitätsszenarien in Abschnitt 10 konkretisieren diese Qualitätsziele" (*the quality scenarios in section 10 make these quality goals concrete*), with a link back from §10 | **neither** — "Utility Tree" is the only named method |
| [Urbo](https://gitlab.opencode.de/stadt-soest/city-app/soest-city-app/-/blob/main/docs/architecture/arc42.md) | ~3 417 B | `10.1 Quality Tree`, `10.2 Quality Scenarios` | yes — a **Mermaid `mindmap` block**, the only machine-readable tree in the eleven. Root "Quality" → 6 branches → exactly 3 leaves each, two levels below the root; **not** cross-linked to the QS ids | **12** (QS-1…QS-12) | table `ID \| Quality Attribute \| Scenario \| Target` — a separate response-measure column, SEI-like without being the six-part form | 4 number · **7 gate** · 1 prose | **partially restated**: the tree's branch names repeat §1.2's four goals verbatim *and silently add two more* (Security, Performance) that §1.2's ranked list does not contain. No cross-reference in either direction | neither, though the attribute vocabulary echoes ISO 25010 |
| [geOrchestra Gateway](https://docs.georchestra.org/gateway/en/latest/arc42/quality_requirements/) | **12 136 B — the largest §10 of the eleven** | `Quality Attributes Overview` (a flat numbered list of 8), then 8 `## … Requirements` groups split into 20 `### <sub-attribute>` sections | **none** — no tree, no nesting beyond the headings, just the flat 8-item list | **40** — two per sub-attribute | **prose**: a `**Requirement**` line, a `**Scenarios**` list of two, and a separate `**Measures**` list per sub-attribute | at the 20-group level: 5 number-bearing · ~14 **gate** · ~1 prose | **neither pointer nor restatement — a second, independent taxonomy.** §10's eight attributes overlap its "Architecture Goals" page's nine goals only on *Security*; no link runs either way | neither |

**Quotations that carry the classification.**

- Urbo's most measure-bearing and vaguest, from the verbatim `Target` column: **QS-2** →
  "Response time < 500ms"; **QS-3** → "Core features accessible without training".
- Urbo's **QS-9** is the single clearest precedent in the eleven for a tool gate used as a response
  measure: `Target` = "Feature + Adapter pattern followed; **Nx boundaries enforced**" — an
  architectural rule whose measure is the build-time boundary check that enforces it. **QS-7** →
  "Request rejected with 401; audit logged" and **QS-11** → "Single codebase produces web, PWA, iOS,
  Android builds" are the same shape.
- DokChess's most measure-bearing: **W01** — "Jemand mit Grundkenntnissen in UML und Schach möchte
  einen Einstieg in die Architektur von DokChess finden. Lösungsstrategie und Entwurf erschließen
  sich ihr oder ihm **innerhalb von 15 Minuten**." (*Someone with basic UML and chess knowledge
  wants an entry point into DokChess's architecture; the solution strategy and design become clear
  to them within 15 minutes.*) Its vaguest: **W02** — "…und findet ihn **unverzüglich** in der
  Dokumentation." (*…and finds it immediately in the documentation.*) — no number, no check.
- DokChess's six gate scenarios are the chess-rule conformance ones (F01-F04, Z01-Z02): the engine's
  response is decided by the rules of chess, an external conformance standard, with no number
  anywhere.
- geOrchestra's most measure-bearing: "Under normal load, the Gateway should add no more than 50ms
  of latency to requests. … For authentication operations, 95% of requests should complete within
  500ms", with `Measures:` "Latency monitoring at percentiles (50th, 95th, 99th)". Its vaguest: "The
  login page should be intuitive and support multiple authentication methods", measured by
  "Responsive design… Clear error messages… Accessible user interface components".

**Footnotes to 17.2.**

1. *geOrchestra's measures are per sub-attribute, not per scenario.* Its `**Measures**` list is
   shared by the two scenarios under a heading, so its figures are counted over the **20 groups**
   and are not comparable row-for-row with the other seven. It is therefore excluded from the
   per-scenario totals in section 18 and reported separately there.
2. *Two independent passes disagreed on DokChess's §10.2 count* — 13 from the rendered pages, 15
   from the Hugo source in `github.com/DokChess/website_de`. The source figure is used. DokChess's
   rendered pages also refused verbatim reproduction on copyright grounds during one pass, which is
   why the source repository was read instead.
3. *Urbo's twelve `Target` cells were reproduced verbatim from the raw Markdown* and classified
   directly; its figures do not rest on a summary.
4. *DokChess's and geOrchestra's byte figures* are `wc -c` over the source Markdown; Urbo's is the
   approximate span between headings in a single-file document.
5. *No quality-tree image was read.* Three of the five trees in the eleven are PNGs
   (`doctoolchain-v4`, `biking2`, DokChess); their structure is reported from surrounding prose and
   alt text only, and their depth is **[unverified]**.

---

## 18 What the tables support — mechanical observations

**§10 is the section most likely to be missing.** **Three of eleven have none** — fin-mig,
status.arc42.org and NFDI4Earth — against two of eleven for §2 and zero for §1. arc42 licenses an
absent §10.2 on exactly one condition, that §10.1's summary is itself "precise, specific enough and
measurable"; **none of the three meets it**, because none has a §10.1 either. All three moved the
material to §1.2 instead.

**Scenario counts, over the eight that have a §10.** 19, 2, 11, 7, 4, 15, 12, 40. Sorted: 2, 4, 7,
11, 12, 15, 19, 40. **Median 11.5, mean 13.75, total 110.** Not one document approaches the ">100
different quality scenarios" arc42 says it sees in real-world systems
([tip 10-1](https://docs.arc42.org/tips/10-1/)); the largest, geOrchestra Gateway at 40, is the only
one above 20.

**The quality tree survives in five of eight — and three of those five are images.** Present:
docToolchain v4 (mindmap PNG), biking2 (PNG), TPU (**a table**), DokChess (PNG), Urbo (**a Mermaid
`mindmap` block**). Absent: MaMa, HtmlSC (which says why — "For our small example, such a quality
tree is overly extensive"), geOrchestra Gateway. So **only two of the eight documents publish a tree
a reader can diff, search or copy**, and both of them chose text over a drawing. That matches
arc42's own retraction: [tip 10-2](https://docs.arc42.org/tips/10-2/), "we favor a simple table
instead of the graphics".

**Six of eight use a table for the scenarios; only two give the measure its own column.**
docToolchain v4 (`Response Measure`) and Urbo (`Target`). Everywhere else the measure is a clause
inside a free-text cell, or absent. **One of eight uses the SEI long form** (docToolchain v4).
**Zero of eleven use the Q42 short form** — the three-part Context / Source-Stimulus / Metric
structure arc42 marks as its own house style is not visible in a single published document here.

**A gate is at least as common as a number, and every document uses one.** Over the **70 scenarios
that can be classified individually** (the eight minus geOrchestra Gateway, whose measures are
shared per group), **31 carry a gate** — a test, a named check, an exit code, a byte comparison, a
rule-conformance criterion, a tool-enforced boundary — and **28 carry a number**; 14 carry neither.
Three scenarios carry both, which is why the figures sum past 70. **All seven of those documents use
a gate at least once.** geOrchestra Gateway, counted at its own granularity, points the same way
harder: roughly 14 of its 20 measure groups are mechanisms rather than numbers.

**Duplication: half the field does what the template forbids.** Of the eight with a §10, **four
reference §1.2 without restating it** (docToolchain v4, MaMa, HtmlSC, DokChess — DokChess with links
in both directions), **three restate it** (TPU, which admits it in a note; Urbo, which repeats the
names and silently adds two goals §1.2 never ranked; geOrchestra Gateway, which runs a second,
unconnected taxonomy), and **one says nothing about it** (biking2).

**ISO 25010 or Q42 is named in one of eight** — docToolchain v4, "The quality tree organizes
requirements by ISO 25010 categories". NFDI4Earth names ISO 25010:2011 too, but in §1.2, having no
§10 to name it in.

### 18.1 What a section author gets wrong

**The measure loses its column, and then it loses itself.** Six of eight bury the measure inside a
prose cell. The two that give it a column — docToolchain v4's `Response Measure` and Urbo's `Target`
— are also the two with the fewest unmeasurable scenarios (zero and one). Separating the column is
what forces the question; a free-text cell lets an author stop at the response.

**The vaguest scenarios cluster on the qualities that resist a number.** HtmlSC has five prose
scenarios out of seven, all correctness/flexibility/safety assertions; DokChess's four are
maintainability and portability; geOrchestra's one prose-only group is usability. The pattern is not
that these qualities cannot be measured — DokChess measures maintainability at "innerhalb von 15
Minuten" and Urbo measures maintainability at "New module added without modifying existing modules"
— but that authors reach for a number, fail to find one, and then write nothing rather than reaching
for a gate.

**The tree gets drawn instead of written.** Three of five are PNGs whose depth cannot be read from
the source, which means the one job arc42 still credits the tree with — showing which branch has no
scenarios ([tip 10-4](https://docs.arc42.org/tips/10-4/)) — cannot be checked by anyone reading the
repository. Urbo's Mermaid block is the counter-example and costs nothing.

**Restating §1.2 in §10 is the commonest structural error**, committed by three of eight against an
explicit template instruction. Its worst form is geOrchestra Gateway's: two quality taxonomies in
one document, eight attributes in §10 against nine goals on the goals page, overlapping on one term
and cross-referenced nowhere — so a reader cannot tell which list governs.

**§10 is dropped, and its content reappears in §1.2 unbounded.** All three documents with no §10
moved their quality material into §1.2, and two of those three then overshoot arc42's maximum of
five goals (status.arc42.org at 6). Deleting §10 does not delete the requirements; it removes the
place that was supposed to absorb the overflow, and §1.2 inherits it.

---

## What the evidence supports

The findings restated as what they license, in a form that lifts into a row of the `hld-author`
skill. §1's and §2's rows are in
[`39-arc42-goals-and-constraints.md`](39-arc42-goals-and-constraints.md).

### §10 — Quality requirements

**The rule that binds it hardest.** A §10 scenario must **let a reader decide whether it is
fulfilled** — "Quality scenarios make quality requirements concrete and allow to decide whether they
are fulfilled (in the sense of acceptance criteria). Ensure that your scenarios are specific and
measurable." Everything else in §10 is negotiable; this is not. Its immediate corollary is the
second-hardest rule: **§10 references §1.2's top goals, it does not restate them** — "they should
only be referenced here" — and §10's own content is the *rest*, the lesser-importance and
nice-to-have requirements.

**What arc42 says about quantity.** **No bound, in either direction.** arc42 publishes an
expectation of many (">100 different quality scenarios" in real systems; "dozens (or even
hundreds)") and exactly one quantity *rule*, which permits none: **"If these summary descriptions
are already precise, specific enough and measurable, you may skip section 10.2."** The "top 3-5"
that saturates the corpus belongs to §1.2 and never to §10. On **scenario kinds** arc42 publishes
**three** — usage, change, failure — in the tips and the FAQ, though the template's own block names
only the first two.

**The form it sanctions.**

- **Two scenario forms, both named and attributed.** The **short form**, "favoured in the Q42
  model": *Context/Background → Source/Stimulus → Metric/Acceptance Criteria*. The **long form**,
  "favoured by the SEI and [Bass+21]": *Scenario ID, Scenario Name, Source, Stimulus, Environment,
  Artifact, Response, Response Measure*. **"Stimulus → response → measure" is not arc42's
  phrasing** — it is a three-term compression of the FAQ's four-term decomposition that drops the
  context both published forms make first-class. If a three-part form is wanted, arc42's own is
  **Context → Stimulus → Measure**.
- **§10.1 is a table** — "a simple table in which each line contains a category or topic and a short
  description" — with a mindmap as the sanctioned alternative. **A quality tree is not required**,
  its graphical form is **explicitly deprecated** by arc42 ("we favor a simple table instead of the
  graphics"), no depth is published for it, and its one surviving use is as a checklist that makes a
  missing scenario visible. ISO 25010 supplies the *generic* tree; yours is the *specific* one.
- **§10 names no other section.** arc42 relates it to §1.2 densely and to §4 once (via
  [tip 10-8](https://docs.arc42.org/tips/10-8/)'s `Quality goal | Scenario | Solution approach |
  Risk` evaluation table). It **never** names §6, §8 or §11. The only mechanism it offers for tying
  a scenario to a building block is the SEI form's own `Artifact` field.

**Can a test, a check or a tool gate be the measure? Yes.** arc42 never requires a number. Its words
are "**the criteria** or metric", "measurable **in some fashion**", and "testable and verifiable";
and it publishes, under its own authorship, measures that are a test suite ("Correctness of all
checks is ensured by automated positive and negative tests" — its own §10.2 example), a conformance
criterion across named targets ("usable with the database systems DB2, Oracle and MySQL without
source code modifications"), and a content invariant. Practice agrees decisively: across the 70
individually classifiable scenarios in the eleven documents, **31 carry a gate against 28 carrying a
number**, and every document that has a §10 uses a gate at least once. The strongest single
precedent is Urbo's QS-9, whose `Target` is "Feature + Adapter pattern followed; **Nx boundaries
enforced**" — an architectural rule measured by the build-time check that enforces it.

**Two conditions the licence comes with.**

1. **Name the gate.** arc42's own model answer does not say "fast tests"; it says "All unit tests
   for a subsystem complete in less than 180 seconds" *and* "Test execution time is measured on
   standard CI/CD infrastructure" ([tip 1-15](https://docs.arc42.org/tips/1-15/)). A duration
   without a rig is not decidable, and neither is a gate without a named suite, rule or command.
2. **A gate is not a licence for an adjective.** "Avoid buzzwords"; the scenario must still allow
   someone to decide. "The conformance suite passes" and "the lint rule holds" qualify; "the library
   is maintainable" does not.

That arc42 licenses *precisely* a conformance suite or a lint rule is **[unverified]** in one narrow
sense: no arc42 page uses the words *tool gate*, *conformance suite* or *linter*. The conclusion
rests on arc42's own published examples and on its "criteria / in some fashion / testable and
verifiable" wording, not on a sentence naming the case.

---

## Sources

### arc42 template — `arc42/arc42-template`, default branch HEAD, read 2026-09-14

- https://github.com/arc42/arc42-template/blob/master/EN/adoc/10_quality_requirements.adoc
- https://github.com/arc42/arc42-template/blob/master/EN/adoc/01_introduction_and_goals.adoc — for the §1.2 ↔ §10 division
- https://github.com/arc42/arc42-template/tree/master/dist — `arc42-template-EN-plain-markdownStrict.zip`, the published Markdown a user receives

### docs.arc42.org

- https://docs.arc42.org/section-10/ · https://docs.arc42.org/section-1/
- Tips: https://docs.arc42.org/tips/10-1/ · https://docs.arc42.org/tips/10-2/ · https://docs.arc42.org/tips/10-3/ · https://docs.arc42.org/tips/10-4/ · https://docs.arc42.org/tips/10-5/ · https://docs.arc42.org/tips/10-6/ · https://docs.arc42.org/tips/10-7/ · https://docs.arc42.org/tips/10-8/
- Tips on the §1 side: https://docs.arc42.org/tips/1-12/ · https://docs.arc42.org/tips/1-14/ · https://docs.arc42.org/tips/1-15/ · https://docs.arc42.org/tips/1-16/ · https://docs.arc42.org/tips/1-18/
- Worked examples: https://docs.arc42.org/examples/quality-htmlsc-2/ · https://docs.arc42.org/examples/quality-tpu-1/ · https://docs.arc42.org/examples/quality-requirements-1/

### faq.arc42.org

- https://faq.arc42.org/questions/C-10-1/ · https://faq.arc42.org/questions/C-10-2/ · https://faq.arc42.org/questions/C-10-3/ · https://faq.arc42.org/questions/C-10-4/ · https://faq.arc42.org/questions/C-10-5/
- https://faq.arc42.org/questions/C-1-2/ · https://faq.arc42.org/questions/C-1-7/ · https://faq.arc42.org/questions/B-4/

### quality.arc42.org (Q42)

- https://quality.arc42.org — 191 quality-characteristic entries, 37 aliases, 150 example requirements
- https://quality.arc42.org/requirements/quick-unit-tests — the entry [tip 1-15](https://docs.arc42.org/tips/1-15/) quotes in full

### examples.arc42.org — the eight hosted documents

- https://examples.arc42.org/systems/doctoolchain-v4/10-quality-requirements/
- https://examples.arc42.org/systems/biking/10-quality-requirements/
- https://examples.arc42.org/systems/mama/10-quality-requirements/
- https://examples.arc42.org/systems/htmlsc/10-quality-requirements/
- https://examples.arc42.org/systems/tpu/10-quality-requirements/
- https://examples.arc42.org/systems/fin-mig/10-quality-requirements/
- https://examples.arc42.org/systems/status.arc42.org/10-quality-requirements/
- https://examples.arc42.org/systems/nfdi4earth/10-quality-requirements/
- https://examples.arc42.org/systems/rgcat/ — inspected and **excluded**: only an index page, no per-section files

### The three documents arc42 links to but does not host

- DokChess (German) — https://www.dokchess.de/10_qualitaetsanforderungen/ · .../01_qualitaetsbaum/ · .../02_qualitaetsszenarien/ · https://www.dokchess.de/01_einfuehrung/02_qualitaetsziele/ ; source at https://github.com/DokChess/website_de
- Urbo — https://gitlab.opencode.de/stadt-soest/city-app/soest-city-app/-/blob/main/docs/architecture/arc42.md
- geOrchestra Gateway — https://docs.georchestra.org/gateway/en/latest/arc42/quality_requirements/ · https://docs.georchestra.org/gateway/en/latest/arc42/architecture_goals/ ; source at https://github.com/georchestra/georchestra-gateway

### Companion note

- [`39-arc42-goals-and-constraints.md`](39-arc42-goals-and-constraints.md) — §1 and §2,
  findings 1-10, over the same eleven documents
