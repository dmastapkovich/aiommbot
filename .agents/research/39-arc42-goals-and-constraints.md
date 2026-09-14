# 39. arc42 §1 and §2 as the template defines them and as public projects keep them

**Question.** What does arc42 require of §1 (Introduction and goals) and §2 (Architecture
constraints) — in the template's own words, in its tips and in its FAQ — and how do published
arc42 documents actually keep those two sections?

Gathered for [#108](https://github.com/dmastapkovich/aiommbot/issues/108), serving
[#37](https://github.com/dmastapkovich/aiommbot/issues/37), which writes §1, §2 and §10 of this
project's architecture document. The `hld-author` skill carries measured rows for §6, §7 and §8
only; this note and its companion produce the rows for §1, §2 and §10.

**This note is one half of a split pair.** §10 is measured in
[`40-arc42-quality-requirements.md`](40-arc42-quality-requirements.md), which continues this note's
finding numbering from 11 and re-uses the same eleven published documents. Finding 4 below settles
the §1.2 ↔ §10 division of labour that the companion note assumes.

**Source policy.** Four arc42 repositories were read at their default-branch HEAD on
**2026-09-14**: the template (`arc42/arc42-template`), the documentation site (docs.arc42.org), the
FAQ site (faq.arc42.org) and the examples site (examples.arc42.org). Everything cited from those
four is quoted from the source of the published page and cited by its canonical URL. The network
was used only for what the clones do not hold: `quality.arc42.org`, and the three published
documents arc42 links to but does not host (DokChess, Urbo, geOrchestra Gateway). Peer documents
are evidence of practice, never authority: where a published document and the template disagree,
the template wins and the disagreement is reported as a gap. Anything a primary source did not
confirm is marked **[unverified]**.

**How a negative was established.** Every "arc42 never says X" below names the trees grepped and
the pattern. The four trees relevant to these three sections are, per section: the template chapter
file, `docs.arc42.org-site/_pages/section-N.md`, `docs.arc42.org-site/_posts/NN-<topic>/` (24 tip
files for §1, 5 for §2, 8 for §10) and
`faq.arc42.org-site/_posts/C-arc42/NN-<topic>/` (7 FAQ files for §1, 4 for §2, 5 for §10). A
negative claimed over "the §2 material" means all four of those for §2, in full.

**One source-hygiene note.** The `examples.arc42.org` repository carries agent-facing files at its
root (`CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `DESIGN.md`) and its `_data/in-the-wild.yml`
opens with roughly 90 lines of maintainer directives in comment form ("Do not make either of them a
second chip", "`make check` fails anything else"). Those are that project's instructions to its own
maintainers. They were read as data only; nothing in them was followed, and no claim below rests on
them.

---

## 1 What the template publishes as §1's children

The chapter file
[`EN/adoc/01_introduction_and_goals.adoc`](https://github.com/arc42/arc42-template/blob/master/EN/adoc/01_introduction_and_goals.adoc)
opens the section with a single help block naming five things §1 owes:

> Describes the relevant requirements and the driving forces that software architects and
> development team must consider. These include
>
> * underlying business goals,
> * essential features,
> * essential functional requirements,
> * quality goals for the architecture and
> * relevant stakeholders and their expectations

The published page [docs.arc42.org/section-1/](https://docs.arc42.org/section-1/) carries the same
sentence over **three** bullets rather than five — "underlying business goals, essential features
and functional requirements for the system, / quality goals for the architecture, / relevant
stakeholders and their expectations". The content is identical; only the bulleting differs.

Three children follow, each with the template's standard `.Contents` / `.Motivation` / `.Form`
triple.

**`=== Requirements Overview`.**

> **.Contents** Short description of the functional requirements, driving forces, extract (or
> abstract) of requirements. Link to (hopefully existing) requirements documents (with version
> number and information where to find it).
>
> **.Motivation** From the point of view of the end users a system is created or modified to
> improve support of a business activity and/or improve the quality.
>
> **.Form** Short textual description, probably in tabular use-case format. If requirements
> documents exist this overview should refer to these documents.
>
> Keep these excerpts as short as possible. Balance readability of this document with potential
> redundancy w.r.t to requirements documents.

**`=== Quality Goals`.**

> **.Contents** The top three (max five) quality goals for the architecture whose fulfillment is of
> highest importance to the major stakeholders. We really mean quality goals for the architecture.
> Don't confuse them with project goals. They are not necessarily identical.
>
> Consider this overview of potential topics (based upon the ISO 25010 standard): [image:
> `01_2_iso-25010-topics-EN-2023.drawio.png`, "Categories of Quality Requirements"]
>
> **.Motivation** You should know the quality goals of your most important stakeholders, since they
> will influence fundamental architectural decisions. Make sure to be very concrete about these
> qualities, avoid buzzwords. If you as an architect do not know how the quality of your work will
> be judged...
>
> **.Form** A table with quality goals and concrete scenarios, ordered by priorities

**`=== Stakeholders`.**

> **.Contents** Explicit overview of stakeholders of the system, i.e. all person, roles or
> organizations that
>
> * should know the architecture
> * have to be convinced of the architecture
> * have to work with the architecture or with code
> * need the documentation of the architecture for their work
> * have to come up with decisions about the system or its development
>
> **.Motivation** You should know all parties involved in development of the system or affected by
> the system. Otherwise, you may get nasty surprises later in the development process. These
> stakeholders determine the extent and the level of detail of your work and its results.
>
> **.Form** Table with role names, person names, and their expectations with respect to the
> architecture and its documentation.

### 1.1 Which child actually ships a table

Only one, and it is not the one the ticket most needs. §1.3 is the sole child of §1, §2 or §10 for
which the template ships a real table skeleton with named columns:

```asciidoc
[options="header",cols="1,2,2"]
|===
|Role/Name|Contact|Expectations
| _<Role-1>_ | _<Contact-1>_ | _<Expectation-1>_
| _<Role-2>_ | _<Contact-2>_ | _<Expectation-2>_
|===
```

The columns are, verbatim: **`Role/Name` | `Contact` | `Expectations`**
([`01_introduction_and_goals.adoc`](https://github.com/arc42/arc42-template/blob/master/EN/adoc/01_introduction_and_goals.adoc)).

§1.2's `.Form` says "A table with quality goals and concrete scenarios, ordered by priorities" but
the template ships **no such table and names no columns for it**. Extracting
`arc42-template-EN-plain-markdownStrict.zip` from
[`dist/`](https://github.com/arc42/arc42-template/tree/master/dist) confirms what a user actually
receives: under `# Introduction and Goals` the file carries `## Requirements Overview` and
`## Quality Goals` as bare headings with nothing beneath them, and one HTML table with
`Role/Name` / `Contact` / `Expectations` under `## Stakeholders`.

The docs site is one step less bare: it ships fill-in lines the AsciiDoc template does not, namely
`### _<insert requirements overview>_`, `### _< insert table of quality goals here>_` and
`### _<complete the stakeholder table:>_` followed by a three-column Markdown table
([docs.arc42.org/section-1/](https://docs.arc42.org/section-1/)). So even on the site the §1.2
"table of quality goals" exists as an instruction, never as a shape.

**Consequence for #37.** For §1.2 the column set is the author's to choose. arc42 constrains only
its content (goals, concrete scenarios) and its ordering (by priority).

---

## 2 The quantity arc42 publishes for §1.2 — "three to five" is arc42's own number

Ticket #37's wording "three to five" is **not** this project's invention. It is a faithful
paraphrase of arc42's own published number, which appears in six places across all three
publications and nowhere contradicted.

Grepped `arc42-template/EN`, `docs.arc42.org-site/_pages`, `docs.arc42.org-site/_posts` and
`faq.arc42.org-site/_posts` (all of them, all sections) for
`top (three|3)|three \(max|3-5|3 to 5|three to five|max(imum)? five|handful`. Every hit relevant to
quality goals is quoted below; the only other hits were tip 3-5 and question C-3-5, whose
permalinks merely contain the digits.

| Where | Sentence, verbatim |
|---|---|
| Template §1.2 `.Contents` | "The top three (max five) quality goals for the architecture whose fulfillment is of highest importance to the major stakeholders." |
| [docs.arc42.org/section-1/](https://docs.arc42.org/section-1/) §1.2 Content | "The top three (max five) quality goals for the architecture whose fulfillment is of highest importance to the major stakeholders." |
| [Tip 1-16](https://docs.arc42.org/tips/1-16/) (title) | "Describe only the top 3-5 quality goals in the introduction!" |
| [Tip 1-16](https://docs.arc42.org/tips/1-16/) (body) | "Here, in section 1.2, you describe only a handful (top 3-5) of these requirements." |
| [Tip 1-18](https://docs.arc42.org/tips/1-18/) | "Section 1 (here) shall only contain a _handful_ of the most important or critical of such requirements." |
| [Tip 10-2](https://docs.arc42.org/tips/10-2/) | "We propose to keep arc42 section 1.2 (quality goals) short, there you show only the top 3-5 quality goals, with priorities." |
| [Question C-1-1](https://faq.arc42.org/questions/C-1-1/) | "Document the top 3-5 quality requirements by showing scenarios" |
| [Question C-10-5](https://faq.arc42.org/questions/C-10-5/) | "arc42 suggests to document or specify the top 3-5 quality requirements in section 1.2" |
| [Question B-4](https://faq.arc42.org/questions/B-4/) (minimal arc42) | "3-5 central quality requirements, expressed in scenarios." |

Two things the number carries that a bare "three to five" loses:

1. **Three is the target, five is the cap.** The template's phrasing is "the top three (max
   five)" — not "three to five". A document with three goals is on arc42's centre line; one with
   five is at its published limit.
2. **The count binds §1.2 only, never §10.** Question B-4 shows the same number doing a second
   job — it is arc42's answer to "what is the minimal amount of an arc42 documentation", where the
   3-5 scenarios are one of five items that must always exist. So the number is simultaneously
   arc42's *ceiling* for §1.2 and its *floor* for a whole document.

**A second quantity, for §1.1.** [Question C-1-1](https://faq.arc42.org/questions/C-1-1/) publishes
a matching bound on the functional side: "Briefly explain the major (max 3-5) use-cases, features
or functions." This is the only number arc42 publishes for §1.1, it appears in the FAQ only, and
neither the template nor the section page repeats it.

---

## 3 Where a quality goal comes from — arc42 names models, mandates none

arc42 names two catalogues and calls both of them *checklists* or *overviews of potential topics*.
It never requires that a quality goal belong to a named category.

**ISO 25010.** The template's §1.2 help block introduces the ISO picture with "Consider this
overview of **potential** topics (based upon the ISO 25010 standard)"; the section page softens it
further to "**For example** the ISO 25010:2023 standard provides an overview of potential topics"
([docs.arc42.org/section-1/](https://docs.arc42.org/section-1/)).
[Tip 1-14](https://docs.arc42.org/tips/1-14/) is titled "Use checklists for quality requirements!"
and says "With its hierarchical representation, the ISO standard 25010:2023 provides a **good
checklist** for top-level quality 'topics'." It then publishes arc42's own nine-item shortlist,
which is *not* ISO's: availability, modifiability, maintainability, reliability / robustness,
performance (runtime efficiency), security, safety, usability, testability.
[Question C-1-2](https://faq.arc42.org/questions/C-1-2/) is weaker still: "It **sometimes helps**
to take a look at the (very generic) ISO-25010 _software product quality_ tree".

**Q42 is an arc42 publication, by arc42's own words.**
[docs.arc42.org/section-10/](https://docs.arc42.org/section-10/) states it directly: "Since January
2023, **arc42 provides** a pragmatic quality model, that proposes to _label_ quality requirements,
with _hashtags_ or _labels_ like #flexible, #efficient, #usable, #operable, #testable, #secure,
#safe" and #reliable." The template's §10 `.Further Information` block links it as "the extensive
Q42 quality model on https://quality.arc42.org", and its §10.2 `.Examples` block names it as the
place to find "detailed examples of quality requirements". [quality.arc42.org](https://quality.arc42.org)
is by Gernot Starke — arc42's co-creator — under CC BY-SA 4.0, and publishes four things: quality
characteristics with definitions and aliases, example requirements with measurable targets,
architectural solutions, and standards/regulations. It states its own size as **191 entries, 37
aliases** of quality characteristics and **150 examples** of requirements.

**arc42's own pages disagree about Q42's size**, which is worth knowing before citing a number:
[question C-1-2](https://faq.arc42.org/questions/C-1-2/) says "more than 75 specific examples",
[question C-10-2](https://faq.arc42.org/questions/C-10-2/) says "more than 100 specific examples",
[tip 1-14](https://docs.arc42.org/tips/1-14/) says "around 150 real-world examples" and
[tip 1-15](https://docs.arc42.org/tips/1-15/) says "around 150 example requirements, plus some 190
quality characteristics". The site itself is the authority; the FAQ figures are stale.

**What ISO and Q42 are *for*, in arc42's telling.** Not to classify a goal after the fact, but to
find one in the first place. [Tip 1-15](https://docs.arc42.org/tips/1-15/) states the method
plainly: "Asking stakeholders 'what are your quality requirements?' usually produces silence, or
buzzwords. Hardly anybody can write a measurable quality requirement from a blank page. Reacting to
one, though, is easy." [Tip 10-4](https://docs.arc42.org/tips/10-4/) turns the tree into a gap
finder: "In case some of the major branches of your tree have no scenarios, that might be an
indicator for missing scenarios."

**Negative.** No arc42 page requires a quality goal to be tagged, categorised or traced to a
standard. Grepped the whole of `docs.arc42.org-site/_pages`, `docs.arc42.org-site/_posts` and
`faq.arc42.org-site/_posts` together with the template's chapters 1 and 10 for
`iso.?25010|iso.?9126|Q42|quality.arc42` and read every hit: every one is phrased as "consider",
"for example", "it sometimes helps", "a good checklist", "as suggested by" or "proposes". ISO 9126
is never mentioned anywhere in the three trees — zero matches for `9126`. The categories are open.

---

## 4 §1.2 against §10 — what each owes, and every sentence pointing one at the other

This is the sharpest duplication risk in the ticket, and arc42 addresses it directly — then
partially contradicts itself.

**The rule, from the template.**
[`EN/adoc/10_quality_requirements.adoc`](https://github.com/arc42/arc42-template/blob/master/EN/adoc/10_quality_requirements.adoc),
§10 `.Content`:

> This section contains all relevant quality requirements.
>
> **The most important of these requirements have already been described in section 1.2. (quality
> goals), therefore they should only be referenced here.** In this section 10 you should also
> capture quality requirements with lesser importance, which will not create high risks when they
> are not fully achieved (but might be _nice-to-have_).

Every sentence in which one section points at the other:

| Source | Sentence, verbatim |
|---|---|
| Template §10 `.Content` | "The most important of these requirements have already been described in section 1.2. (quality goals), therefore they should only be referenced here." |
| [docs.arc42.org/section-1/](https://docs.arc42.org/section-1/) §1.2 Form | "See `[section 10 (Quality Requirements)](/section-10/)` for a complete overview of quality requirements." |
| [Tip 1-16](https://docs.arc42.org/tips/1-16/) | "All the other qualities goals and requirements can either be found in the requirements specification or in the quality tree in arc42 section 10." |
| [Tip 1-18](https://docs.arc42.org/tips/1-18/) (title) | "Defer detailed and complete quality requirements to arc42 section 10!" |
| [Tip 1-18](https://docs.arc42.org/tips/1-18/) (body) | "Describe the complete detailed quality requirements in arc42 section 10. Section 1 (here) shall only contain a _handful_ of the most important or critical of such requirements. Collect the rest in arc42 section 10 (quality requirements), with detailed and specific scenarios." |
| [Tip 10-1](https://docs.arc42.org/tips/10-1/) (title) | "Keep the quality goals in arc42-section 1.2 short!" |
| [Tip 10-1](https://docs.arc42.org/tips/10-1/) (body) | "Move details, especially of quality requirement, to _this_ section 10." |
| [Tip 10-2](https://docs.arc42.org/tips/10-2/) | "We propose to keep arc42 section 1.2 (quality goals) short, there you show only the top 3-5 quality goals, with priorities. Here, in arc42 section 10, we go into more detail: Show your most important quality goals and -requirements" |
| [Question C-1-7](https://faq.arc42.org/questions/C-1-7/) | "arc42 section 1.2 contains the high-priority quality requirements / arc42 section 10 contains _the rest_, structured as a quality tree." |
| [Question C-10-5](https://faq.arc42.org/questions/C-10-5/) | "arc42 suggests to document or specify the top 3-5 quality requirements in section 1.2 - right at the start of the documentation. That's helpful, as some of these requirements might influence the most important, fundamental (or often expensive...) architecture decisions. […] In real-world systems we often find >100 different quality scenarios, way too many to digest _all-at-once_. That's why arc42 proposes to document/specify this multitude in arc42 section 10..." |

**What each owes, settled.**

- **§1.2 owes:** the top three (max five) architecture quality goals, each with a concrete
  scenario, ordered by priority, concrete rather than buzzword. It is the only one of the two that
  carries a *count*.
- **§10 owes:** all the rest — the lesser-importance and nice-to-have requirements — plus a
  *reference* back to §1.2's goals rather than a restatement of them. It is the only one of the two
  that carries the word *measurable*.

**The contradiction, stated plainly.** The template says the §1.2 goals "should **only be
referenced** here". [Tip 10-2](https://docs.arc42.org/tips/10-2/) says of §10 "Show your most
important quality goals and -requirements", which reads as a licence to restate them. The tip is
older (2016) than the current template text and is itself flagged "(deprecated!)" in its title for
a different reason (see §15). **Where the two disagree, the template governs: §10 references, it
does not restate.** Section 17's table shows which published documents follow which.

**A third destination.** [Tip 1-17](https://docs.arc42.org/tips/1-17/) offers §4 as an alternative
home: "it helps to document these quality goals and the resulting decisions in a consolidated
table. We propose that you put such a table into the arc42 section 4 (solution strategy) […] Here,
in arc42-section 1.2 (quality goals), you then only add a reference." So arc42 sanctions §1.2 being
a pointer at §4 as well as §10.

**Where the word "measurable" lives.** Grepped the §1 material (template chapter 1, section-1.md,
all 24 tips in `_posts/01-requirements/`, all 7 files in `faq .../01-requirements/`) for
`measurab|measure|metric`: **three hits, all in tip 1-15**, and all of them about Q42's examples
rather than about §1.2's own duty. The same grep over the §10 material returns nine hits including
the three normative ones. §1.2's own standard is not "measurable" but the template's "A table with
quality goals and **concrete scenarios**" plus "be very concrete […] avoid buzzwords". The
measurability bar is §10's.

---

## 5 Stakeholders — what an entry owes

**The template's columns, verbatim:** `Role/Name` | `Contact` | `Expectations`
([`01_introduction_and_goals.adoc`](https://github.com/arc42/arc42-template/blob/master/EN/adoc/01_introduction_and_goals.adoc)),
with two placeholder rows `_<Role-1>_ | _<Contact-1>_ | _<Expectation-1>_`. The `.Form` line reads
"Table with role names, person names, and their expectations with respect to the architecture and
its documentation."

**What an entry owes, from the FAQ.**
[Question C-1-4](https://faq.arc42.org/questions/C-1-4/) is the only arc42 page that separates
required from optional, and it does so typographically: "**Bold** information should be present,
the other parts are optional."

| Field | Status | arc42's own gloss |
|---|---|---|
| **Name/Role** | required | "who or which part of an organization has an interest in the system or its architecture? Sometimes you name specific people, quite often you'll stick to roles" |
| Knowledge | optional | "What do these stakeholders know about the system or its associated processes?" |
| **Expected deliverables** | required | "What do these stakeholders expect from the architecture or its documentation? Please don't confuse this with the _system requirements_." |
| _Relevance_ (priority) | optional | "Some stakeholders will be relevant or required for production acceptance or sign-off - but: Explicitly stating relevance or priority might frustrate, irritate or even instigate those with lower priorities…" |
| **Contact** | required | "As trivial as a phone number or email address, so you or the team can contact this stakeholder." |
| Comment | optional | "Any other information people might need concerning this stakeholder." |

**The one thing an entry must not be.** [Question C-1-5](https://faq.arc42.org/questions/C-1-5/)
exists solely to prevent the commonest error: the Expectations column holds *documents the
stakeholder needs*, not *requirements on the system*. Its examples are "a detailed description with
sample data and code snippets", "a _decision log_ of architecturally relevant decisions (arc42
section 9)", "technical detail of the required database and middleware configuration". [Tip
1-20](https://docs.arc42.org/tips/1-20/) puts it as a question to ask: "Ask for expected content,
form and eventually required details."

**What the tips add.**

- [Tip 1-19](https://docs.arc42.org/tips/1-19/) publishes a 40-odd-role catalogue to search
  against, explicitly including "external service providers, external partners […] neighboring
  systems".
- [Tip 1-21](https://docs.arc42.org/tips/1-21/) publishes **two** concrete tables: a *minimal*
  one with columns `Role` | `Expectation`, and a *detailed* one with `Role` | `Contact` |
  `Relevance for approval` | `Expectation`. Neither matches the template's own three columns
  exactly — the minimal one drops Contact, the detailed one adds Relevance.
- [Tip 1-22](https://docs.arc42.org/tips/1-22/) sanctions **omitting** the table: "Do not document
  the stakeholder table if your management already maintains a consistent stakeholder overview […]
  you should only cross-reference it." With a caveat: "in our experience, project managers focus
  rather on organizational information about stakeholders (e.g., contact details and contact
  persons). In arc42 we need information about the specific *expectations*."
- [Tip 1-23](https://docs.arc42.org/tips/1-23/) offers an interest/influence matrix as a
  time-pressure substitute, and ends "Ideally, you have a stakeholder table plus such a
  classification." It also warns the matrix may be better kept private.
- [Question C-1-3](https://faq.arc42.org/questions/C-1-3/) gives the reason the table exists at
  all, including one that matters here: "Architecture stakeholders are sometimes _forgotten_ during
  conventional requirements analysis, e.g. dev-teams of external interfaces, auditors or developers
  themselves - these people or organizations will not have requirements concerning the system
  itself, but its architecture or architecture documentation."

### 5.1 The §1.3 ↔ §3 overlap: a measured negative

**No arc42 page relates the §1.3 stakeholder table to §3's external partners or neighbouring
systems, and none warns about restating one in the other.**

Grepped the §1 material — template chapter 1, `_pages/section-1.md`, all 24 files in
`_posts/01-requirements/`, all 7 files in `faq .../C-arc42/01-requirements/` — for
`neighbou?r|external partner|communication partner|section.?3|context`. Four hits total: two inside
[tip 1-19](https://docs.arc42.org/tips/1-19/)'s stakeholder catalogue (the words "external
partners" and "neighboring systems" as *stakeholder roles*), and two unrelated ordinary uses of the
word "context" (tip 1-8, tip 1-15). **Zero hits name section 3.**

Grepped from the other side — template chapter 3, `_pages/section-3.md`, `_posts/03-context/`,
`faq .../C-arc42/03-context/` — for `stakeholder`. Five hits, every one of them treating
stakeholders as *readers* of §3 ("All stakeholders should understand which data are exchanged with
the environment of the system"), none relating §3's partners back to the §1.3 table.

So the relation is not merely undocumented, it runs the wrong way: tip 1-19 actively pushes
neighbouring systems and external partners **into** the §1.3 table, while §3 asks for the same
neighbours as context elements, and no arc42 page ever mentions that these are the same entities.
The author of #37 has to draw that line without arc42's help. [Question
C-1-3](https://faq.arc42.org/questions/C-1-3/) supplies the only usable discriminator, and it is
about *what they want* rather than *who they are*: a §1.3 entry exists because someone needs
something **from the architecture documentation**; a §3 element exists because something crosses
the system boundary.

---

## 6 §1.1 when the requirements live elsewhere

arc42 sanctions a pointer, but never a pointer **instead of** an extract. It asks for both, and it
names the trade-off out loud.

**Template §1.1 `.Contents`:** "Short description of the functional requirements, driving forces,
extract (or abstract) of requirements. **Link to (hopefully existing) requirements documents (with
version number and information where to find it).**"

**Template §1.1 `.Form`:** "Short textual description, probably in tabular use-case format. **If
requirements documents exist this overview should refer to these documents.** Keep these excerpts
as short as possible. **Balance readability of this document with potential redundancy w.r.t to
requirements documents.**"

That last sentence is arc42 conceding the duplication rather than forbidding it: the excerpt stays,
it is only kept short.

**The size bound.** [Tip 1-1](https://docs.arc42.org/tips/1-1/): "Our rule of thumb: **Less than
one page, if possible.** This page may contain a diagram if it supports the content. You should
reference requirement documents if present." The same tip names the two exceptions — "For systems
with complex or extensive business requirements" and "For systems without an existing (and
reasonable) requirements documentation" — and [question
C-1-6](https://faq.arc42.org/questions/C-1-6/) adds a third: "where some (unconspicious)
requirements have _huge_ impact on certain architecture decisions".

**The pointer must be addressable.** [Tip 1-5](https://docs.arc42.org/tips/1-5/) is the one that
matters for a repository-hosted project: "In case you are referencing existing requirements in the
architecture documentation, e.g. to justify a design decision, you need to make sure that these
requirements can be **identified uniquely, by a short key or something similar**. […] If your
requirements are managed by a tool (e.g. an issue tracker), you can use those ID's - **with some
tools you even have stable URLs**." An issue tracker with stable URLs is arc42's own named case.

**Form options arc42 publishes for §1.1**, all optional and all illustrative: a tabular use-case
format (template `.Form`), a requirements *cluster* table with columns `Requirements cluster` |
`Description` ([tip 1-4](https://docs.arc42.org/tips/1-4/)), an activity diagram
([tip 1-6](https://docs.arc42.org/tips/1-6/)), a BPMN diagram
([tip 1-7](https://docs.arc42.org/tips/1-7/)), a plain numbered list
([tip 1-8](https://docs.arc42.org/tips/1-8/)), PlantUML activity text
([tip 1-9](https://docs.arc42.org/tips/1-9/)) and an exemplary business process model
([tip 1-10](https://docs.arc42.org/tips/1-10/)). [Tip
1-2](https://docs.arc42.org/tips/1-2/) bounds the abstraction: "Limit yourself to a level of
abstraction so that also outsiders are able to get an overview of the major tasks in a short period
of time." [Question C-1-1](https://faq.arc42.org/questions/C-1-1/) bounds the count: "Briefly
explain the major (max 3-5) use-cases, features or functions."

---

## 7 §2's groups — four names, every one of them hedged

The template's §2 `.Form`
([`EN/adoc/02_architecture_constraints.adoc`](https://github.com/arc42/arc42-template/blob/master/EN/adoc/02_architecture_constraints.adoc)):

> Simple tables of constraints with explanations. **If needed** you can subdivide them into
> technical constraints, organizational and political constraints and conventions (e.g. programming
> or versioning guidelines, documentation or naming conventions)

[Tip 2-5](https://docs.arc42.org/tips/2-5/), titled "Differentiate different categories of
constraints!", carries the same four with the same hedge: "**If necessary**, differentiate between
technical, organizational and political constraints or overlapping conventions (e.g., programming
guidelines, documentation-, naming- or organisational conventions)."

[Question C-2-2](https://faq.arc42.org/questions/C-2-2/) gives the fullest gloss and drops
"political" to reach **three**, again hedged:

> **If needed**, differentiate between the following types of constraints:
>
> * **Organizational** constraints: E.g. compliance to (standard) processes, budget, time, required
>   information flows, required (management) reporting structures, adherence to certain
>   documentation templates or conventions...
> * **Technical** constraints: Usage of specific hardware, middleware, software-components,
>   adherence to specific technical or architectural decisions (e.g. use of specific frameworks or
>   libraries)
> * **Conventions**, e.g. programming style, naming conventions or similar stuff.

**Prescriptive or illustrative? Illustrative, unambiguously.** All three sentences that publish the
groups begin with "if needed" or "if necessary". The only arc42 page that states a group as a duty
is [tip 2-3](https://docs.arc42.org/tips/2-3/) — "Document organizational constraints!" — and its
body reverts to explanation ("Therefore disclose these types of constraints"). Two further tips
name where to *look*: [tip 2-1](https://docs.arc42.org/tips/2-1/) ("If you don't know any
constraints of your system, start looking at other systems within the organization") and [tip
2-4](https://docs.arc42.org/tips/2-4/) ("guidelines from the managements or the organisation itself
regarding hardware, operations, technology selection, use of products, frameworks or reference
architectures").

An author of #37 may therefore group §2 any way the material warrants, or not group it at all.

---

## 8 Constraint against decision — is a constraint by definition something the team did not choose?

**No. arc42 defines a constraint by its *effect*, not by its *origin*, and it names the team's own
conventions as one of its constraint categories.**

This is the finding the ticket most depends on, so the whole evidence base is laid out.

### 8.1 The definition, in all three publications

| Source | Definition, verbatim |
|---|---|
| Template §2 `.Contents` | "Any requirement that constraints software architects in their freedom of design and implementation decisions or decision about the development process. These constraints sometimes go beyond individual systems and are valid for whole organizations and companies." |
| [docs.arc42.org/section-2/](https://docs.arc42.org/section-2/) Content | "Any requirement that constrains software architects in their freedom of design and implementation decisions or decision about the development process. […]" (same sentence, typo corrected) |
| [Question C-2-1](https://faq.arc42.org/questions/C-2-1/) | "Constraints restrict your freedom in decisions, concerning the system or any associated processes." |

Not one of the three says *who* must impose it. The test each states is the same: **does it remove
freedom from a later decision?**

### 8.2 What arc42 says about origin

Only two sentences in the entire §2 material speak to origin, and both hedge:

- [Question C-2-1](https://faq.arc42.org/questions/C-2-1/): "Such constraints are **often** imposed
  by organizations across multiple IT systems." — *often*, not *always*.
- Template §2 `.Contents`: "These constraints **sometimes** go beyond individual systems and are
  valid for whole organizations and companies." — *sometimes*.

**Grep evidence.** Grepped all four arc42 trees (`arc42-template`, `docs.arc42.org-site`,
`faq.arc42.org-site`, in full, every section) for `self.imposed|self imposed`: **zero matches**.
arc42 has no concept named "self-imposed constraint" — but neither does it have any sentence
excluding one. Grepped the §2 material (template chapter 2, `_pages/section-2.md`, all 5 tips in
`_posts/02-constraints/`, all 4 files in `faq .../C-arc42/02-constraints/`) for `imposed|impose`:
**exactly one match**, question C-2-1's "often imposed", quoted above.

### 8.3 The "conventions" category settles it

arc42 publishes *conventions* as one of its named constraint categories, and every example it gives
of a convention is a rule a team normally writes for itself:

- Template `.Form`: "conventions (e.g. **programming or versioning guidelines, documentation or
  naming conventions**)"
- [Tip 2-5](https://docs.arc42.org/tips/2-5/): "conventions (e.g., **programming guidelines,
  documentation-, naming- or organisational conventions**)"
- [Question C-2-2](https://faq.arc42.org/questions/C-2-2/): "**Conventions**, e.g. **programming
  style, naming conventions** or similar stuff."

arc42 names the category and never asks who authored the convention. A team's own coding guideline
is, by arc42's own enumeration, a §2 constraint.

### 8.4 The test arc42 actually publishes for admission

Origin is not the filter; [question C-2-3](https://faq.arc42.org/questions/C-2-3/) is:

> At first - **try to avoid documentation of constraints, as somebody else might already have
> documented them. Refer or link to existing documentation.**
>
> Document the constraints that:
>
> * shape or shaped important architectural or technical decisions,
> * help people to better understand your architecture

Two filters, then, and a prior instruction to link rather than copy. A row earns §2 if it *shaped
decisions* and *aids understanding* — not if it came from outside.

### 8.5 What this licenses for #37, and what it does not

**Licensed.** A project rule such as "one distribution" or "zero suppressions" belongs in §2 when
it functions as a rule that binds *subsequent* decisions — that is what the template's Motivation
means by "Architects should know exactly where they are free in their design decisions and where
they must adhere to constraints." arc42's own "conventions" category is precisely this class.

**The line that separates §2 from §9, and it is inference, not quotation.** [Question
C-2-3](https://faq.arc42.org/questions/C-2-3/) says a §2 constraint "shape**d** important
architectural or technical decisions" — the constraint is *upstream* of the decision. So the same
sentence can appear in two places doing two jobs: the ADR records *the choice and its reasoning*
(§9), while §2 records *the binding it now imposes on everything after it*. **[unverified]** — no
arc42 page states this split; the §2 material never names section 9 at all (see §9 below).

**Counter-evidence, reported in full.** The centre of gravity of arc42's own examples is external.
All four examples in [question C-2-1](https://faq.arc42.org/questions/C-2-1/) are externally
imposed — "System has to be operated by data-center XYZ, as our company has a long-term contract
with them", "Part of software/hardware development has to be off-shored to our Asian subdivision",
"Our operational database system needs to be IBM DB2", "System has to be implemented in Java". [Tip
2-1](https://docs.arc42.org/tips/2-1/) sends you outward to find constraints; [tip
2-3](https://docs.arc42.org/tips/2-3/) frames them as things "unpopular with development teams";
[tip 2-4](https://docs.arc42.org/tips/2-4/) sources them from "the managements or the organisation
itself". A reader steeped only in the examples would conclude §2 is for external impositions. A
reader of the definitions and of the conventions category would not. **The definitions govern.**

---

## 9 §2's relation to §4, §8, §9 and §10 — a measured negative, with one thing arc42 does say

**arc42 never names another section from within §2's material.**

Grepped the §2 material — the template's chapter 2 file, `_pages/section-2.md`, all 5 files in
`_posts/02-constraints/`, all 4 files in `faq .../C-arc42/02-constraints/` — for
`section.?(4|8|9|10)|solution strategy|crosscutting|decision`. Eight hits, and every single one is
the generic word "decision" inside a definition or a tip ("restrict your freedom in decisions",
"limit the freedom of design or implementation decisions", "shape or shaped important architectural
or technical decisions", "adherence to specific technical or architectural decisions"). **Zero hits
name section 4, 8, 9 or 10, the solution strategy, or crosscutting concepts.** So arc42 does not
say where the consequence of a constraint is written, and does not relate §2 to §10's quality
requirements.

**What arc42 does say about consequences: keep them with the constraint.**
[Tip 2-2](https://docs.arc42.org/tips/2-2/), titled "Clarify the consequences of constraints!":

> You should clarify the *consequences* of constraints, e.g. resulting (additional) costs or
> effort.
>
> If constraints bring *unreasonable* consequences (e.g., can only be satisfied with excessively
> high costs), you should negotiate about them with the relevant stakeholders.

**May §2 carry motivation? Yes — it is required by the form.** The template's `.Form` is "Simple
tables of constraints **with explanations**". The explanation column is not optional decoration; it
is the second half of the published form.

**May a constraint be challenged or removed? Yes, explicitly.** Template §2 `.Motivation`:
"Constraints must always be dealt with; **they may be negotiable, though.**" And [question
C-2-4](https://faq.arc42.org/questions/C-2-4/), titled "Can/shall we negotiate constraints?":

> Should some constraints prove to be especially **unfavorable**, **risky** or even **expensive**
> for your system or its development, you should definitely try to negotiate them.

Its worked example is a company-wide "software has to be developed in Java" constraint that should
be argued down for a smart-card driver. This matters for #8's question: **negotiability is not a
discriminator between imposed and self-chosen constraints.** arc42 expects even organisation-wide
impositions to be negotiable, so a rule the team can revise by amending its own ADR is no less a
constraint for being revisable.

---

## 10 The published form for §2 — arc42 says table, ships nothing, and publishes a list

Three answers that do not agree, and the disagreement is itself the finding.

**What arc42 says.** "Simple tables of constraints with explanations" (template `.Form`,
[docs.arc42.org/section-2/](https://docs.arc42.org/section-2/)).

**What arc42 ships.** Nothing. §2 is the only one of these three sections with **no children and no
skeleton at all**. In the template's AsciiDoc chapter the help block is the entire file. In the
published Markdown (`arc42-template-EN-plain-markdownStrict.zip` from
[`dist/`](https://github.com/arc42/arc42-template/tree/master/dist)) `# Architecture Constraints` is
followed immediately by `# Context and Scope` — not one subheading, not one table row. The docs site
adds only the fill-in line `### _<insert relevant constraints>_`.

**Columns: arc42 publishes none for §2.** There is no `|===` block in the chapter file and no table
in `_pages/section-2.md`. The word "explanations" in the `.Form` line is the only hint at a second
column, and it names no header.

**What arc42 publishes as its one worked example is a bullet list.**
[examples/constraints-1/](https://docs.arc42.org/examples/constraints-1/), the HTML Sanity Checker,
is captioned by arc42 itself:

> Key constraints can often be explained as **simple enumeration in plain text**.

and its body is four bullets — "platform-independent and should run on the major operating systems
(Windows™, Linux, and Mac-OS™) / integrated with the Gradle build tool / runnable from the command
line / developed under a liberal open-source license". No IDs, no explanations column, no groups.

**Net.** §2's form is the least constrained of the three. A table with a constraint and an
explanation is the stated default; a plain enumeration is explicitly sanctioned by arc42's own
example; groups are optional; column names are the author's.

---

## 17 The measured half — §1 and §2 across eleven published documents

Eleven documents, the same eleven two earlier notes in this catalogue used: the eight complete
documents republished on [examples.arc42.org](https://examples.arc42.org), plus three arc42 links
to but does not host — DokChess (German), Urbo and geOrchestra Gateway. §10 is measured over the
same eleven in [`40-arc42-quality-requirements.md`](40-arc42-quality-requirements.md) section 17.

`_systems/` in the examples repository also holds **`rgcat`**, which is *not* one of the eleven and
is excluded. The exclusion is now independently confirmed rather than assumed: `rgcat/` contains
only `index.md` (4 936 bytes) and an `images/` directory — it has no per-section files at all, so
there is no §1, §2 or §10 to measure. Nothing found during this pass argues for adding it.

**Provenance caveat, which the byte counts depend on.** The eight hosted documents are
*republications* by the examples.arc42.org maintainers, not always the authors' own files. Several
were converted from another medium — `fin-mig` from a German `.docx` and a book chapter,
`nfdi4earth` from a 2024 PDF, `mama` from OmniGraffle and XMind originals — and in four places the
hosted page is an **editorial note reporting that the original has no such section** rather than
content. Those four are marked *(editorial note)* below and are counted as absent, not as short.
Byte sizes are `wc -c` over the whole hosted file including its 30-45 byte YAML front matter.

### 17.1 §1 — Introduction and goals

| Document | §1 bytes | §1.1 form | §1.2 count | §1.2 form | Ranked? | Scenario per goal? | §1.3 filled? | §1.3 rows | §1.3 columns |
|---|---|---|---|---|---|---|---|---|---|
| [docToolchain v4](https://examples.arc42.org/systems/doctoolchain-v4/01-introduction-and-goals/) | 5 404 | bullet list, bold labels | **5** | table | yes — `Priority` 1-5 | yes, each cross-linked to a QS-id | yes | 6 | `Role/Name` \| `Contact` \| `Expectations` |
| [biking2](https://examples.arc42.org/systems/biking/01-introduction-and-goals/) | 4 107 | prose + "Main features" bullets | **5** | table | implicit — `Nr.` 1-5, no priority wording | no — motivation prose only | yes | 4 | `Role / Name` \| `Goal / Boundaries` |
| [MaMa-CRM](https://examples.arc42.org/systems/mama/01-introduction-and-goals/) | 21 391 | prose, incl. a 9-step walkthrough | **3** | prose under `Prio N:` headers | yes — explicit `Prio 1/2/3` | yes, concrete | yes | 6 | `Role` \| `Description` \| `Goal, Intention` |
| [HTML Sanity Checker](https://examples.arc42.org/systems/htmlsc/01-introduction-and-goals/) | 6 250 | prose + numbered list + 2 tables | **6** | table | yes, with ties — three rows at 1, two at 2 | yes, one sentence each | yes, thin — one cell empty | 3 | `Role` \| `Description` \| `Goal, Intention` |
| [Traffic Pursuit Unit](https://examples.arc42.org/systems/tpu/01-introduction-and-goals/) | 3 595 | table `Id`\|`Requirement`\|`Explanation` + use-case diagram | **3** | table | yes — `Prio` 1-3 | no — motivational prose; scenarios live in §10 as SC-ids | yes | 6 | `Role/Name` \| `Contact` \| `Expectations` |
| [fin-mig (M&M)](https://examples.arc42.org/systems/fin-mig/01-introduction-and-goals/) | 5 944 | bullet list, 4 items | **2** | table | yes — `Priority` 1-2 | yes, concrete | yes | 4 | `Role` \| `Description, goal and intention` |
| [status.arc42.org](https://examples.arc42.org/systems/status.arc42.org/01-introduction-and-goals/) | 2 131 | bullet list with `F-001`…`F-005` ids | **6** | **bullet list** | **no** — flat, unordered | yes — each bullet embeds thresholds | **no table** — prose reconstruction of 2 implicit groups | — | — |
| [NFDI4Earth](https://examples.arc42.org/systems/nfdi4earth/01-introduction-and-goals/) | 3 523 | 4 numbered use cases + pointer to §4 | **3** | table | **no** — flat, with a stated intent to prioritise later | **no** — ISO 25010 dictionary definitions | yes, minimal | 2 | `Role` \| `Expectations` |
| DokChess | see 17.3 | — | — | — | — | — | — | — | — |
| Urbo | see 17.3 | — | — | — | — | — | — | — | — |
| geOrchestra Gateway | see 17.3 | — | — | — | — | — | — | — | — |

Notes on the hosted eight:

- **Numbering is the minority practice.** Three of eight keep arc42's `1.1 / 1.2 / 1.3` numbering
  (`mama`, `htmlsc`, `fin-mig`, the last only partially); five drop it to bare
  `## Requirements Overview` / `## Quality Goals` / `## Stakeholders`.
- **Renames.** `mama` writes §1.3 as "Stakeholder" (singular); `tpu` shortens §1.1 to
  "Requirements"; `biking` and `status.arc42.org` retitle the columns of the stakeholder table
  entirely.
- **Additions arc42 does not ask for.** `mama` adds `1.2.3 Non-Goals (Out of Scope)` and two
  subsections under §1.3; `fin-mig` adds a `### Non-Goals` block and three unnumbered preamble
  sections ("Purpose of the System", "Starting Situation of the Existing Data", "Intended
  Audience"); `tpu` puts a second, unnumbered `Priority | Goal` table of five *project* goals above
  §1.1 — the exact confusion the template warns about ("We really mean quality goals for the
  architecture. Don't confuse them with project goals.").
- **Real names appear in three of eight.** `doctoolchain-v4` ("Ralf D. Mueller and core team"),
  `biking` (the author himself), `tpu` (three named organisations). `mama` and `fin-mig` both
  footnote a *deliberate* pseudonym for the client; `htmlsc` names none and says so.
- **Not one of the eight left a template placeholder** (`<Role-1>`, `...`) in place. Where §1.3 is
  absent it is absent deliberately and explained, not abandoned mid-fill.

### 17.2 §2 — Architecture constraints

| Document | §2 bytes | Form | Groups used, verbatim | Count | Rationale column? | Carries something the team chose itself? | Cross-refs |
|---|---|---|---|---|---|---|---|
| [docToolchain v4](https://examples.arc42.org/systems/doctoolchain-v4/02-architecture-constraints/) | 3 243 | tables under sub-headings | `Technical Constraints`, `Organizational Constraints`, `Conventions` | **17** (6+5+6) | yes — `Explanation` | **yes, nearly all** — "Groovy (JVM) \| Primary implementation language (ADR-1)"; "MIT License"; "Architecture Decision Records \| Significant decisions are documented as ADRs with Pugh Matrix evaluation against quality goals" | §10 (QS-14), §9 (ADR ids) |
| [biking2](https://examples.arc42.org/systems/biking/02-architecture-constraints/) | 3 420 | tables; technical group sub-divided by bold rows *inside* the table | `Organizational Constraints`, `Conventions` (+ in-table "Software and programming", "Operating system", "Hardware") | **15** (TC1-5, OC1-6, C1-4) | yes — `Background and / or motivation` | **yes, all** — "TC1 \| Implementation in Java \| The application should be part of a Java 8 and Spring Boot show case"; "OC5 \| Testing \| Use JUnit… and JaCoCo… at least 90%"; "C2 \| Coding conventions \| … enforced through Checkstyle" | none |
| [MaMa-CRM](https://examples.arc42.org/systems/mama/02-architecture-constraints/) | 1 475 | definition list + bullet lists, **no table** | `General Constraints`, `Software Infrastructure Constraints`, `Operational constraints` | ~**12** (3+6+3) | yes — inline, every item | mixed — "Use Oracle(tm) as database: InDAC holding company has negotiated a favorable deal…" is imposed; "Linux operating system (preferably RedHat Enterprise Linux…)" is a preference; "InDAC prefers iterative development processes **but does not impose them**" is explicitly non-binding | none |
| [HTML Sanity Checker](https://examples.arc42.org/systems/htmlsc/02-architecture-constraints/) | **758** | bullet list | none | **6** | no — occasional inline parenthetical | **yes, every row** — "implemented in Java or Groovy"; "integrated with the Gradle build tool"; "developed under a liberal open-source license" | none |
| [Traffic Pursuit Unit](https://examples.arc42.org/systems/tpu/02-architecture-constraints/) | **334** | table `Id` \| `Description` | none | **2** | folded into `Description` | **no — nothing self-chosen at all**; both rows are cost ceilings: "C1 \| … the production price will not exceed a given limit"; "C2 \| The cost of the development efforts shall not exceed a given limit" | none |
| [fin-mig (M&M)](https://examples.arc42.org/systems/fin-mig/02-architecture-constraints/) | 2 067 | table + bullets + one prose sentence | `2.1 Technical Constraints`, `2.2 Organizational Constraints`, `2.3 Conventions` | ~**18** | yes — `Explanation` | **yes** — "Programming languages \| Java, because of the existing know-how in the development team"; "CM Synergy for version control, and compliance with the Sun Java coding guidelines". Also records *absences*: "Reference architectures \| None available", "Coding guidelines \| None", "Libraries, frameworks and components \| Free choice." | none |
| [status.arc42.org](https://examples.arc42.org/systems/status.arc42.org/02-architecture-constraints/) | **304** *(editorial note)* | — | — | **0** | — | — | §1 ("stated as a quality goal in section 1 rather than recorded here separately") |
| [NFDI4Earth](https://examples.arc42.org/systems/nfdi4earth/02-architecture-constraints/) | 3 702 | one flat table, grouping done **per row** | none as headings; a `Type` column combining `technical` / `organisational` / `strategic` / `conventions` | **15** | yes — `Explanation` | mixed — "5 \| Architecture team \| organisational \| Software decisions … are made by the NFDI4Earth architecture team…" is self-imposed governance; "1 \| NFDI4Earth Proposal" and "14 \| Hosting at TU Dresden" are externally imposed | **§9** — "Constraints 2 and 7–11 are also the criteria against which every individual software decision is weighed" |
| DokChess | see 17.3 | — | — | — | — | — | — |
| Urbo | see 17.3 | — | — | — | — | — | — |
| geOrchestra Gateway | see 17.3 | — | — | — | — | — | — |

### 17.3 The three documents arc42 links to but does not host

These three are not on examples.arc42.org, so they were fetched over the network on 2026-09-14.
Two fetch passes were run independently and reconciled; where they disagreed, the raw source file
settled it, and the disagreements are recorded in the footnotes rather than hidden.

| Document | §1 size | §1.1 form | §1.2 count | §1.2 form | Ranked? | Scenario per goal? | §1.3 filled? | §1.3 rows | §1.3 columns |
|---|---|---|---|---|---|---|---|---|---|
| [DokChess](https://www.dokchess.de/01_einfuehrung/) (German) | 3 270 B over three sub-pages | prose + two bullet lists ("Was ist DokChess?", "Wesentliche Features") | **5** | table | **yes, but softly** — no priority column; the intro says "die Reihenfolge eine grobe Orientierung bezüglich der Wichtigkeit vorgibt" (*the order gives a rough indication of importance*) | **no** — one motivation sentence each, scenarios deferred to §10 by link | yes | 4 | `Wer?` \| `Interesse, Bezug` |
| [Urbo](https://gitlab.opencode.de/stadt-soest/city-app/soest-city-app/-/blob/main/docs/architecture/arc42.md) | ~2 208 B within one file | prose + two bullet lists ("Main Features", "User Requirements") | **4** | table | implicit — `Nr.` 1-4, no priority wording | **no** — a `Motivation` sentence each | yes | 4 | `Role` \| `Contact` \| `Key Expectations` |
| [geOrchestra Gateway](https://docs.georchestra.org/gateway/en/latest/arc42/) | 2 161 B + 4 462 B over **two** pages | prose — a numbered "Key Requirements" list of 6 plus a responsible-for / not-responsible-for split under "System Scope" | **9** | **prose**, one heading per goal, each with `Goal` / `Rationale` / `Approaches` | **two tiers only** — "Primary Goals" (5) and "Secondary Goals" (4), no ordering within a tier | **no** — but every goal carries a rationale *and* a bulleted list of implementation approaches | yes | 4 | `Role` \| `Description` \| `Expectations` |

DokChess's five goals each carry the quality characteristic in the name itself — "Zugängliches
Beispiel (Analysierbarkeit)", "Einladende Experimentierplattform (Änderbarkeit)", "Bestehende
Frontends nutzen (Interoperabilität)", "Akzeptable Spielstärke (Funktionale Eignung)", "Schnelles
Antworten auf Züge (Effizienz)" — an ISO-25010-flavoured vocabulary used without citing the
standard.

**geOrchestra Gateway has no `1.1 / 1.2 / 1.3` numbering at all**, and its §1 material is split
across two sibling pages: `introduction.md` carries the overview, requirements, stakeholders and
scope; `architecture_goals.md` carries what arc42 would call §1.2. The chapter index lists the
second chapter as "Architecture Goals", not "Architecture Constraints".

| Document | §2 size | Form | Groups used, verbatim | Count | Rationale column? | Carries something the team chose itself? |
|---|---|---|---|---|---|---|
| [DokChess](https://www.dokchess.de/02_randbedingungen/) | 3 984 B over three sub-pages | three tables, one per group | `2.1 Technische Randbedingungen`, `2.2 Organisatorische Randbedingungen`, `2.3 Konventionen` — arc42's canonical three-way split | **15** (4 + 7 + 4) | yes, on every row — `Erläuterungen, Hintergrund` | **mixed, and it is the only one of the eleven where the mix is clean.** Genuinely external: "Betrieb auf Windows Desktop Betriebssystemen \| Standardausstattung von Notebooks bei Mitarbeitern des Schulungsunternehmens zum Zeitpunkt der Konzeption" (*the standard notebook issue at the training company at design time*). Self-chosen: "Implementierung in Java \| Einsatz als Beispiel in Java-lastigen Seminaren"; "Kodierrichtlinien für Java \| Java Coding Conventions von Sun/Oracle, geprüft mit Hilfe von **CheckStyle**"; "Veröffentlichung als Open Source \| … GPLv3" |
| [Urbo](https://gitlab.opencode.de/stadt-soest/city-app/soest-city-app/-/blob/main/docs/architecture/arc42.md) | ~3 501 B | three groups, §2.1 sub-divided into three mini-tables | `2.1 Technical Constraints` (→ Software/Programming, Operating System, Hardware), `2.2 Organizational Constraints`, `2.3 Conventions` | **26** (TC1-9, OC1-6, C1-11) — the largest §2 of the eleven | yes — `Background and / or motivation` on all three tables | **yes, essentially the entire section.** "TC1 \| Cross-Platform Citizen App \| The citizen app **must** be developed using Angular, Ionic, and Capacitor…"; "TC4 \| Identity Provider \| Keycloak for OAuth2/OIDC"; "C10 \| Code Formatting \| Prettier (100 char print width, 2-space indent) and ESLint… semicolons required, single quotes, trailing commas". **No law, regulator, client, contract or legacy system is cited anywhere in the section as the source of a constraint.** |
| [geOrchestra Gateway](https://docs.georchestra.org/gateway/en/latest/arc42/) | **0 — the section does not exist** | — | — | **0** | — | — |

**geOrchestra Gateway has no §2.** Confirmed four ways: its `mkdocs.yml` navigation has no
constraints entry between "Architecture Goals" and "Context View"; the `docs/arc42/` directory
listing (13 files) contains no constraints file; a code search for `constraint` scoped to
`docs/arc42/*.md` returns two incidental hits in `index.md` and `risks.md`; and both plausible URLs
— `…/arc42/architecture_constraints/` and `…/arc42/02_architecture_constraints/` — return 404. The
closest material, three bullets under "Technical Context" in `introduction.md`, describes the
current stack rather than stating a rule with a rationale, and sits inside the introduction.

**Footnotes to 17.3.**

1. *Two independent passes disagreed on Urbo's §1.2 and were reconciled against the raw file.* The
   verbatim header row is `| Nr. | Quality | Motivation |` with four numbered rows — not a
   `Priority` / `Rationale` table as one pass reported. All Urbo figures above are from a verbatim
   reproduction of the raw Markdown.
2. *Urbo's §2 is structurally derived from biking2's.* Its column header string
   `Background and / or motivation`, its `TC` / `OC` / `C` identifier scheme and its three in-table
   technical sub-groups are identical to
   [biking2](https://examples.arc42.org/systems/biking/02-architecture-constraints/)'s. The two are
   therefore not independent observations of §2 practice, and any count that treats them as such
   over-weights that shape.
3. *DokChess sizes* are byte counts of the Hugo source files in `github.com/DokChess/website_de`,
   summed over each chapter's sub-pages; the published site renders one page per sub-section. An
   earlier pass over the rendered pages reported 8 rows in §2.2 and 13 scenarios in §10.2; the
   source gives **7** and **15**. The source figures are used.
4. *Urbo's byte figures* come from the raw Markdown fetched over HTTP and are approximate, measured
   as the span between section headings in a single-file document.

---

## 18 What the tables support — mechanical observations

Counts over all eleven documents unless stated. Where a document has no such section it is excluded
from that statistic and the denominator says so.

**§1.2 quality goals — the count.** The eleven publish 5, 5, 3, 6, 3, 2, 6, 3, 5, 4 and 9 goals.
Sorted: 2, 3, 3, 3, 4, 5, 5, 5, 6, 6, 9. **Median 5, mean 4.6.** Seven of eleven fall inside
arc42's "top three (max five)". Three overshoot — HtmlSC and status.arc42.org at 6, geOrchestra
Gateway at 9 — and one undershoots, fin-mig at 2. The median sits exactly on arc42's stated
maximum, not on its stated target of three.

**§1.2 ranking.** **Nine of eleven rank their goals** in some form: an explicit `Priority` / `Prio`
column (docToolchain v4, MaMa, HtmlSC, TPU, fin-mig), an implicit `Nr.` ordering (biking2, Urbo), a
sentence saying the order is meaningful (DokChess), or a two-tier Primary/Secondary bucket
(geOrchestra Gateway). Two do not rank at all: status.arc42.org and NFDI4Earth — and NFDI4Earth
says so in the section itself ("we envision to regularly evaluate the prioritization of the quality
goals").

**§1.2 scenarios.** arc42's `.Form` asks for "a table with quality goals **and concrete
scenarios**". **Five of eleven supply one** (docToolchain v4, MaMa, HtmlSC, fin-mig,
status.arc42.org). Six give a motivation or a dictionary definition instead (biking2, TPU,
NFDI4Earth, DokChess, Urbo, geOrchestra Gateway), four of them deferring the scenario to §10.

**§1.2 form.** Table in eight of eleven; prose or a bullet list in three (MaMa under `Prio N:`
headings, status.arc42.org as bullets, geOrchestra Gateway as one heading per goal).

**§1.3 stakeholders.** **Ten of eleven publish a table**; only status.arc42.org substitutes prose.
**Not one of the eleven left an arc42 placeholder in place** — where the table is absent it is
absent deliberately and explained. Row counts are 6, 4, 6, 3, 6, 4, 2, 4, 4, 4 — **median 4**.

**The `Contact` column is the field authors drop.**
[Question C-1-4](https://faq.arc42.org/questions/C-1-4/) marks Contact as one of three *required*
fields. **Three of eleven keep a Contact column** (docToolchain v4, TPU, Urbo) and **one of eleven
puts a reachable address in it** — Urbo, with three working email addresses. TPU names
organisations, docToolchain names a maintainer. The other eight replaced Contact with a
description, a goal, an interest or nothing.

**arc42's own column triple is almost never used.** `Role/Name | Contact | Expectations` appears
verbatim in **two of eleven** (docToolchain v4, TPU). The other nine each invent their own:
`Role / Name | Goal / Boundaries`, `Role | Description | Goal, Intention`, `Role | Description, goal
and intention`, `Role | Expectations`, `Wer? | Interesse, Bezug`, `Role | Contact | Key
Expectations`, `Role | Description | Expectations`.

**Numbering is a minority practice.** Only three of eleven keep arc42's `1.1 / 1.2 / 1.3` headings
(MaMa, HtmlSC, fin-mig). geOrchestra Gateway not only drops the numbers but splits §1 across two
separate pages.

**Nobody points §1.1 at a requirements document.** arc42's central §1.1 instruction — "Link to
(hopefully existing) requirements documents (with version number and information where to find
it)", reinforced by [tip 1-5](https://docs.arc42.org/tips/1-5/) on stable issue-tracker URLs — is
exercised by **zero of eleven**. Three link to something (biking2 to a blog post for background,
NFDI4Earth forward to §4, MaMa to its own §12 glossary); none links to a requirements document, a
backlog or a tracker. Grepped all eight hosted `01-introduction-and-goals.md` files for
`requirements (document|specification)|refer to|backlog|issue tracker|\[section` and read every hit.

**§2 is missing outright in two of eleven.** status.arc42.org and geOrchestra Gateway have no
architecture-constraints section at all. In status.arc42.org's case the examples.arc42.org editors
say where the material went: "The closest thing to a constraint — no cookies, EU data-privacy
compliance, minimal computing resources — **is stated as a quality goal in section 1** rather than
recorded here separately."

**§2 counts, over the nine that have one.** 17, 15, 12, 6, 2, 18, 15, 15, 26. Sorted: 2, 6, 12, 15,
15, 15, 17, 18, 26. **Median 15, mean ≈ 14.** The largest (Urbo, 26) is six times the size of its
own §1.2; the smallest (TPU, 2) is two cost ceilings and 334 bytes.

**arc42's three-way grouping is the one piece of §2 guidance that is followed.** **Six of nine**
group their constraints under technical / organisational / conventions headings (docToolchain v4,
biking2, fin-mig, DokChess, Urbo, and MaMa with its own names). NFDI4Earth groups per row via a
`Type` column; HtmlSC and TPU do not group at all.

**A rationale is carried in seven of nine.** Under a named column — `Explanation`, `Background and /
or motivation`, `Erläuterungen, Hintergrund` — or inline per item. HtmlSC and TPU carry none.

**§2 is overwhelmingly self-authored in practice.** **Eight of the nine** documents that have a §2
carry at least one rule the team chose for itself, and **four of nine are entirely self-chosen**
(docToolchain v4, biking2, HtmlSC, Urbo). **Exactly one — TPU — contains nothing the team chose**,
and its two rows are externally-set cost ceilings. So the practice of the sample runs directly
against the impression arc42's own §2 examples give, every one of which is an external imposition
(finding 8.5).

**Five of nine name a tool or an automated check inside §2.** biking2 ("JaCoCo… at least 90%",
"enforced through Checkstyle"), DokChess ("geprüft mit Hilfe von CheckStyle"), Urbo ("Prettier…
and ESLint"), fin-mig ("CM Synergy for version control, and compliance with the Sun Java coding
guidelines") and docToolchain v4 ("documented as ADRs with Pugh Matrix evaluation against quality
goals"). A tool gate is already normal §2 content in published practice.

**Only two of nine cross-reference another section from inside §2** — docToolchain v4 to §9 and §10,
NFDI4Earth to §9 ("Constraints 2 and 7–11 are also the criteria against which every individual
software decision is weighed"). This matches arc42, which never asks for such a pointer (finding 9).

### 18.1 What a section author gets wrong

**The stakeholder table loses the one field arc42 marks required.** Ten of eleven publish a table;
three keep a Contact column; one makes it reachable. Authors keep the *shape* of §1.3 and drop the
field that makes it usable.

**§1.2 becomes a glossary of quality words.** Six of eleven give a definition or a motivation where
arc42 asks for a concrete scenario. NFDI4Earth is the clearest case: its three goals are quoted ISO
25010 definitions ("Degree to which the architecture provides functions that meet stated and
implied needs when used under specified conditions"), which say nothing specific about the system.
This is the failure [tip 1-15](https://docs.arc42.org/tips/1-15/) predicts — "usually produces
silence, or buzzwords".

**The count drifts up.** Three of eleven exceed arc42's maximum of five and only one falls below
three. The median lands on the cap.

**Constraints get written as goals when §2 is skipped.** Both documents with no §2 kept the material
— status.arc42.org put it in §1.2, geOrchestra Gateway spread it through an "Architecture Goals"
page and a "Technical Context" bullet list. The section vanishes; the content does not. The cost is
that a rule binding future decisions is now filed as something the system should be good at.

**"Must" is used for choices, without saying who chose.** Urbo's §2 is the extreme: 26 rows phrased
as requirements — "The citizen app **must** be developed using Angular, Ionic, and Capacitor" — with
no law, regulator, client, contract or legacy system named anywhere as the source. DokChess is the
counter-example and the better model: it separates a genuinely external constraint ("Betrieb auf
Windows Desktop Betriebssystemen | Standardausstattung von Notebooks bei Mitarbeitern des
Schulungsunternehmens zum Zeitpunkt der Konzeption") from its own conventions, and gives every row a
rationale. The lesson is not that self-chosen rows are wrong — finding 8 shows arc42 licenses them —
but that a row which does not say where it came from cannot be negotiated, and arc42 expects
constraints to be negotiable ([question C-2-4](https://faq.arc42.org/questions/C-2-4/)).

**Two of the eleven are not independent observations.** Urbo's §2 reproduces biking2's column header
string, identifier scheme and sub-group structure exactly. Any claim about "how §2 is shaped in the
wild" that counts both is counting the same shape twice.

---

## What the evidence supports

The findings restated as what they license, in a form that lifts into a row of the `hld-author`
skill. §10's row is in [`40-arc42-quality-requirements.md`](40-arc42-quality-requirements.md).

### §1 — Introduction and goals

**The rule that binds it hardest.** §1.2 carries only the **architecture** quality goals — "We
really mean quality goals for the architecture. Don't confuse them with project goals" — each one
stated as a *concrete scenario* rather than a word, ordered by priority, with everything beyond the
top few deferred to §10 by reference. A goal that is a noun ("maintainability") and not a situation
has failed the section, and that is the failure six of the eleven published documents commit.

**What arc42 says about quantity.** §1.2: **the top three, maximum five** — arc42's own number,
published in nine places, with three as the target and five as the cap (finding 2). §1.1: **maximum
3-5 use cases, features or functions** ([question C-1-1](https://faq.arc42.org/questions/C-1-1/)),
and **less than one page if possible** ([tip 1-1](https://docs.arc42.org/tips/1-1/)), with three
named exceptions. §1.3: **no count**; arc42 instead publishes a 40-role catalogue to search against
([tip 1-19](https://docs.arc42.org/tips/1-19/)) and a licence to omit the table entirely if someone
else maintains one ([tip 1-22](https://docs.arc42.org/tips/1-22/)).

**The form it sanctions.**

- **§1.1** — short prose, a use-case table, a requirements-cluster table (`Requirements cluster |
  Description`), a numbered list, an activity/BPMN/PlantUML diagram, or an exemplary business
  process model. When requirements live elsewhere, arc42 asks for a **short extract *and* a link**,
  not a link instead of an extract — it names the resulting redundancy and accepts it ("Balance
  readability of this document with potential redundancy"). The link must be to a uniquely
  identifiable item; an issue tracker with stable URLs is arc42's own named case.
- **§1.2** — a table, **ordered by priority**, with a concrete scenario per goal. arc42 publishes
  **no column names** for it, so the columns are the author's; the two column sets arc42 itself
  uses in worked examples are `Priority | Quality Goal | Scenario` and `Prio | Quality Goal |
  Description`. ISO 25010:2023 and Q42 are offered as **checklists for finding goals**, never as a
  taxonomy a goal must belong to.
- **§1.3** — a table. The only columns arc42 ships are **`Role/Name` | `Contact` |
  `Expectations`**; the required fields are **Name/Role, Expected deliverables and Contact**, with
  Knowledge, Relevance and Comment optional. *Expectations* means documents the stakeholder needs
  from the architecture documentation — never requirements on the system. A cross-reference may
  replace the table; an interest/influence matrix may supplement it.

**One thing arc42 leaves to the author.** Nothing in arc42 relates the §1.3 stakeholder table to
§3's external partners, and [tip 1-19](https://docs.arc42.org/tips/1-19/) actively lists
"neighboring systems" and "external partners" as stakeholder roles. The only discriminator the
corpus offers is purpose: a §1.3 entry exists because someone needs something *from the
documentation*; a §3 element exists because something crosses the system boundary (finding 5.1).

### §2 — Architecture constraints

**The rule that binds it hardest.** A §2 row is **anything that removes freedom from a later design,
implementation or process decision** — arc42 defines the section by that effect and never by who
imposed it. Origin is explicitly hedged ("**often** imposed by organizations", "**sometimes** go
beyond individual systems"), the phrase *self-imposed* does not occur anywhere in the three
publications, and **conventions — programming style, naming, versioning, documentation guidelines —
are one of arc42's own named constraint categories**, which is precisely the class a team writes
for itself. The admission test arc42 publishes is
[question C-2-3](https://faq.arc42.org/questions/C-2-3/)'s: a row belongs if it **shaped an
important architectural or technical decision** and **helps people understand the architecture** —
preceded by an instruction to link rather than copy when someone else already documented it.

**So: a project's own rule recorded as an ADR may sit in §2**, in the role of the binding it now
imposes on every later decision, with §9 keeping the choice and its reasoning. That split is
**[unverified]** — arc42 never states it, and the §2 material never names section 9 at all.

**What arc42 says about quantity.** **Nothing.** No upper bound, no lower bound, no target. The only
sizing instruction runs the other way: "At first — try to avoid documentation of constraints, as
somebody else might already have documented them. Refer or link to existing documentation." Two of
the eleven published documents have no §2 at all, and arc42 publishes no sentence making one
mandatory.

**The form it sanctions.**

- **A simple table of constraints with explanations** is the stated form — but arc42 publishes
  **no column names** for §2 and ships **no skeleton at all**: in the generated Markdown template
  the heading is followed immediately by the next chapter.
- **A plain enumeration is equally sanctioned**, by arc42's own worked example: "Key constraints can
  often be explained as **simple enumeration in plain text**"
  ([examples/constraints-1/](https://docs.arc42.org/examples/constraints-1/)).
- **Grouping is optional** — every sentence publishing the groups begins "if needed" or "if
  necessary". The names offered are *technical*, *organizational*, *political* and *conventions*
  (template and [tip 2-5](https://docs.arc42.org/tips/2-5/)), reduced to three in
  [question C-2-2](https://faq.arc42.org/questions/C-2-2/).
- **A rationale is part of the form, not an extra** — "with explanations" — and the *consequence* of
  a constraint belongs beside it, in §2, not in another section
  ([tip 2-2](https://docs.arc42.org/tips/2-2/)).
- **Every row must be challengeable.** "Constraints must always be dealt with; they may be
  negotiable, though", and [question C-2-4](https://faq.arc42.org/questions/C-2-4/) tells you to
  negotiate the unfavourable, risky or expensive ones. Practically this means a row should say
  enough about where it came from that a reader can tell whom to argue with — the failure Urbo's 26
  unattributed "must" rows illustrate.

---

## Sources

### arc42 template — `arc42/arc42-template`, default branch HEAD, read 2026-09-14

- https://github.com/arc42/arc42-template/blob/master/EN/adoc/01_introduction_and_goals.adoc
- https://github.com/arc42/arc42-template/blob/master/EN/adoc/02_architecture_constraints.adoc
- https://github.com/arc42/arc42-template/blob/master/EN/adoc/03_context_and_scope.adoc — grepped for the §1.3 ↔ §3 negative
- https://github.com/arc42/arc42-template/blob/master/EN/adoc/10_quality_requirements.adoc
- https://github.com/arc42/arc42-template/tree/master/dist — `arc42-template-EN-plain-markdownStrict.zip`, the published Markdown a user receives

### docs.arc42.org — section pages

- https://docs.arc42.org/section-1/
- https://docs.arc42.org/section-2/
- https://docs.arc42.org/section-3/ — grepped for the §1.3 ↔ §3 negative
- https://docs.arc42.org/section-10/

### docs.arc42.org — tips

- https://docs.arc42.org/tips/1-1/ · https://docs.arc42.org/tips/1-2/ · https://docs.arc42.org/tips/1-4/ · https://docs.arc42.org/tips/1-5/
- https://docs.arc42.org/tips/1-6/ · https://docs.arc42.org/tips/1-7/ · https://docs.arc42.org/tips/1-8/ · https://docs.arc42.org/tips/1-9/ · https://docs.arc42.org/tips/1-10/
- https://docs.arc42.org/tips/1-12/ · https://docs.arc42.org/tips/1-14/ · https://docs.arc42.org/tips/1-15/
- https://docs.arc42.org/tips/1-16/ · https://docs.arc42.org/tips/1-17/ · https://docs.arc42.org/tips/1-18/
- https://docs.arc42.org/tips/1-19/ · https://docs.arc42.org/tips/1-20/ · https://docs.arc42.org/tips/1-21/ · https://docs.arc42.org/tips/1-22/ · https://docs.arc42.org/tips/1-23/
- https://docs.arc42.org/tips/2-1/ · https://docs.arc42.org/tips/2-2/ · https://docs.arc42.org/tips/2-3/ · https://docs.arc42.org/tips/2-4/ · https://docs.arc42.org/tips/2-5/
- https://docs.arc42.org/tips/10-1/ · https://docs.arc42.org/tips/10-2/ · https://docs.arc42.org/tips/10-4/

### docs.arc42.org — worked examples

- https://docs.arc42.org/examples/quality-requirements-1/ — HTML Sanity Checker §1.2
- https://docs.arc42.org/examples/quality-requirements-3/ — Traffic Pursuit Unit §1.2
- https://docs.arc42.org/examples/constraints-1/ — HTML Sanity Checker §2, the only §2 example arc42 publishes
- https://docs.arc42.org/examples/overview-example-htmlsc-1/ · https://docs.arc42.org/examples/overview-example-3/ — §1.1

### faq.arc42.org

- https://faq.arc42.org/questions/C-1-1/ · https://faq.arc42.org/questions/C-1-2/ · https://faq.arc42.org/questions/C-1-3/
- https://faq.arc42.org/questions/C-1-4/ · https://faq.arc42.org/questions/C-1-5/ · https://faq.arc42.org/questions/C-1-6/ · https://faq.arc42.org/questions/C-1-7/
- https://faq.arc42.org/questions/C-2-1/ · https://faq.arc42.org/questions/C-2-2/ · https://faq.arc42.org/questions/C-2-3/ · https://faq.arc42.org/questions/C-2-4/
- https://faq.arc42.org/questions/C-10-2/ · https://faq.arc42.org/questions/C-10-5/
- https://faq.arc42.org/questions/A-5/ · https://faq.arc42.org/questions/B-1/ · https://faq.arc42.org/questions/B-4/ · https://faq.arc42.org/questions/B-5/
- https://faq.arc42.org/questions/E-5/ · https://faq.arc42.org/questions/H-1/ · https://faq.arc42.org/questions/K-1/ · https://faq.arc42.org/questions/K-2/

### quality.arc42.org (Q42)

- https://quality.arc42.org — the arc42 quality model: 191 quality-characteristic entries, 37 aliases, 150 example requirements
- https://quality.arc42.org/requirements/quick-unit-tests — the entry [tip 1-15](https://docs.arc42.org/tips/1-15/) quotes in full

### examples.arc42.org — the eight hosted documents

Read at `arc42/examples.arc42.org-site` default-branch HEAD on 2026-09-14; each is published at
`https://examples.arc42.org/systems/<slug>/<page>/`.

- https://examples.arc42.org/systems/doctoolchain-v4/ · .../01-introduction-and-goals/ · .../02-architecture-constraints/ · .../10-quality-requirements/
- https://examples.arc42.org/systems/biking/ (biking2)
- https://examples.arc42.org/systems/mama/ (MaMa-CRM)
- https://examples.arc42.org/systems/htmlsc/ (HTML Sanity Checker)
- https://examples.arc42.org/systems/tpu/ (Traffic Pursuit Unit)
- https://examples.arc42.org/systems/fin-mig/ (M&M)
- https://examples.arc42.org/systems/status.arc42.org/
- https://examples.arc42.org/systems/nfdi4earth/
- https://examples.arc42.org/systems/rgcat/ — inspected and **excluded**: only an index page, no per-section files

### The three documents arc42 links to but does not host

- DokChess (German) — https://www.dokchess.de/ · https://www.dokchess.de/01_einfuehrung/ · https://www.dokchess.de/02_randbedingungen/ · https://www.dokchess.de/10_qualitaetsanforderungen/ ; source at https://github.com/DokChess/website_de
- Urbo — https://gitlab.opencode.de/stadt-soest/city-app/soest-city-app/-/blob/main/docs/architecture/arc42.md
- geOrchestra Gateway — https://docs.georchestra.org/gateway/en/latest/arc42/ · .../arc42/introduction/ · .../arc42/architecture_goals/ · .../arc42/quality_requirements/ ; source at https://github.com/georchestra/georchestra-gateway
