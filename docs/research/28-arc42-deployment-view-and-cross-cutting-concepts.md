# 28. arc42 §7 and §8 as the template defines them and as public projects keep them

**Question.** What does arc42 itself require of a deployment view (§7) and a cross-cutting concepts
section (§8), and what is left as §8's *own* content once a project keeps a decision log? The
catalogue rule that a section never restates a decision
([`documentation-style.md`](../documentation-style.md) §6) makes the second half of that question
load-bearing for #40, and the first half decides whether a deployment view carried by a table plus a
container diagram is inside the template.

Gathered for #40, which writes both sections. Sources are primary: the arc42 template in source
form, the `docs.arc42.org` and `faq.arc42.org` site sources, and published arc42 documents read as
source in their repositories. arc42 is not in the local reference cache, so every page was fetched
over the network on 2026-09-10. Where a negative is claimed, the whole repository was downloaded as
a tarball at `HEAD` and grepped in full, because GitHub's code-search endpoint rejects
unauthenticated requests with `401 Unauthorized` in this environment; an exhaustive grep over the
repository tree is the stronger check anyway. Peer documents are evidence of practice, never
authority. Anything a primary source did not confirm is marked **[unverified]**.

## 1 §7 as the template defines it

The template file
[`EN/adoc/07_deployment_view.adoc`](https://github.com/arc42/arc42-template/blob/master/EN/adoc/07_deployment_view.adoc)
states the content as exactly two things:

> 1. technical infrastructure used to execute your system, with infrastructure elements like
>    geographical locations, environments, computers, processors, channels and net topologies as
>    well as other infrastructure elements and
> 2. mapping of (software) building blocks to that infrastructure elements.

[FAQ C-7-1](https://faq.arc42.org/questions/C-7-1/) repeats the same split in four lines — "Your
hardware structure(s), also called technical infrastructure" and "The mapping(s), called deployment,
of your software to this hardware" — and [C-7-3](https://faq.arc42.org/questions/C-7-3/) assigns
them to different authors: infrastructure "will sometimes be created and maintained by stakeholders
responsible for this technical infrastructure", while "the mapping of software to hardware, will
often be documented and maintained by architects and/or the development team".

Three scoping statements bound the section, all from the template file:

- **When it is worth writing at all.** "Especially document a deployment view if your software is
  executed as distributed system with more than one computer, processor, server or container or when
  you design and construct your own hardware processors and chips."
- **How much infrastructure.** "From a software perspective it is sufficient to capture only those
  elements of an infrastructure that are needed to show a deployment of your building blocks.
  Hardware architects can go beyond that and describe an infrastructure to any level of detail they
  need to capture."
- **Environments.** "Often systems are executed in different environments, e.g. development
  environment, test environment, production environment. In such cases you should document all
  relevant environments." The level-1 help adds: "For multiple environments or alternative
  deployments please copy and adapt this section of arc42 for all relevant environments."
  [Tip 7-3](https://docs.arc42.org/tips/7-3/), "Document the various environments!", adds a rule the
  template does not state — document the environments "plus possible differences between them" — and
  names the notation: "The stereotype «executionEnvironment» symbolizes such environments."

The motivation is one sentence — "Software does not run without hardware." — followed by the clause
that matters for §8. The two publications of the template word that clause differently, and the
difference is not cosmetic: the AsciiDoc file reads "This underlying infrastructure can and will
influence a system and/or some cross-cutting concepts. Therefore, there is a need to know the
infrastructure.", while [docs.arc42.org/section-7](https://docs.arc42.org/section-7/) reads "This
underlying infrastructure can and will influence your system and/or some cross-cutting concepts.
Therefore, you need to know the infrastructure." Same content, second person on the site.

**Infrastructure levels open one at a time, and there are only two of them.** The template body is
`=== Infrastructure Level 1` and `=== Infrastructure Level 2`. The level-2 help is one instruction —
"Here you can include the internal structure of (some) infrastructure elements from level 1. Please
copy the structure from level 1 for each selected element." — but the level-2 *body* is not empty:
it ships three named subsections, `==== _<Infrastructure Element 1>_`, `_<Infrastructure Element
2>_` and `_<Infrastructure Element n>_`, each followed by `_<diagram + explanation>_`. The site
version numbers the same children 7.2.1 … 7.2.n. [Tip 7-8](https://docs.arc42.org/tips/7-8/),
"Explain your nodes!", is the page that says what goes in them: nodes with "high importance or
special meaning for the system" must be explained — "what there properties are and why they are so
special for the system or its operation" — and "The arc42 template (section 7) contains subsections
labelled \"Infrastructure element\" - which you can use to document or specify such details."

This is the §5 recursion, but shallower and selective: §5 opens white boxes to any depth, §7 offers
two named levels and refines only *some* elements.
[Tip 7-4](https://docs.arc42.org/tips/7-4/) makes the parallel explicit — "Like in the building
block view (see tip 5-2 (hierarchical building block view)) you can organize and document the
deployment view as a hierarchy."

Level 1 has four fixed slots. The template's help asks to describe, "usually in a combination of
diagrams, tables, and text":

- "distribution of a system to multiple locations, environments, computers, processors, .., as well
  as physical connections between them"
- "important justifications or motivations for this deployment structure"
- "quality and/or performance features of this infrastructure"
- "mapping of software artifacts to elements of this infrastructure"

and the body carries them as `_**<Overview Diagram>**_`, `Motivation::`,
`Quality and/or Performance Features::` and `Mapping of Building Blocks to Infrastructure::`.

**Nothing in §7 is marked mandatory.** The website marks the third slot "(optional) Quality and/or
Performance Features" and shortens the fourth to "Mapping"; the AsciiDoc template marks nothing
optional and keeps the long name. No word of obligation is attached to any of the four in either
version: `must` occurs nowhere in the template file and nowhere on the section page — established by
grepping both files for `\bmust\b` and getting zero matches. So the four slots are the template's
own structure, not a checklist with required entries.

**What "mapping of building blocks to infrastructure" means.**
[Tip 7-5](https://docs.arc42.org/tips/7-5/) narrows it to artifacts, not modules: "Document or
specify the mapping of the building blocks (see arc42 section 5) onto the hardware (more
specifically — the mapping of the _artifacts_ generated/compiled/created from the actual source code
building blocks.). That is called _deployment_. In many cases that can be an m:n mapping, with
several variants of deployment artifacts. Remember to explain these deployment variants."
[FAQ C-7-5](https://faq.arc42.org/questions/C-7-5/) confirms that variants are expected: "Yes, for
example when you have different _stages_ from development to your production environment."
[Tip 7-2](https://docs.arc42.org/tips/7-2/) offers a per-node table whose four rows are
Responsibility, "(technical) characteristics", "associated building blocks — what part of the
software is running on this hardware?" and "reason for selection".

**What §7 pushes elsewhere.** [Tip 7-10](https://docs.arc42.org/tips/7-10/), titled "Leave hardware
decisions to hardware-experts!", is the only page on either section that delegates a whole topic to
other people: "In case you are primarily concerned with _software_ architecture — and there are
different people in your organization caring about hardware and technical infrastructure, leave the
documentation of this infrastructure to them. Include only such information in the software
architecture documentation that's neccessary to understand the associated architecture decisions."
[Tip 7-1](https://docs.arc42.org/tips/7-1/) closes with the same instruction one line long: "Try to
delegate the hardware and infrastructure documentation to the appropriate stakeholders." (Telling
the author to *stop writing* is not unique to §7 — see section 8 below, where §8 does the same three
times.)

The template also hands the top of the view to §3: "Maybe a highest level deployment diagram is
already contained in section 3.2. as technical context with your own infrastructure as ONE black
box. In this section one can zoom into this black box using additional deployment diagrams."

Ten tips are published under `tips/7-*` — 7-1 through 7-10, no gaps, established by listing
`_posts/07-deployment/` in
[`arc42/docs.arc42.org-site`](https://github.com/arc42/docs.arc42.org-site/tree/main/_posts/07-deployment).

## 2 §8 as the template defines it

The template file
[`EN/adoc/08_concepts.adoc`](https://github.com/arc42/arc42-template/blob/master/EN/adoc/08_concepts.adoc)
defines the content in two sentences: "This section describes crosscutting concepts (practices,
patterns, regulations or solution ideas). Such concepts are often related to multiple building
blocks." The motivation is conceptual integrity — "Concepts form the basis for _conceptual
integrity_ (consistency, homogeneity) of the architecture. Thus, they are an important contribution
to achieve inner qualities of your system." — and the template adds why the section exists at all:
"This is the place in the template that we provided for a cohesive specification of such concepts."

[Tip 8-2](https://docs.arc42.org/tips/8-2/), "Concepts are approaches, rules, principles, tactics,
strategies etc...", widens the same definition into a list of nine words practitioners use for what
§8 holds: "approaches", "aspects: like in \"aspect-oriented-programming\"", "concepts: our
favorite", "concerns", "principles", "regulations", "rules", "tactics" and "strategies". Two of
those nine — *regulations* and *rules* — decide sub-question 8; see section 8 below.

**The recommended form is deliberately unfixed.** Three bullets, verbatim:

> * concept papers with any kind of structure
> * example implementations,especially for technical concepts
> * cross-cutting model excerpts or scenarios using notations of the architecture views

The template body is nothing but `=== _<Concept 1>_` / `_<explanation>_` repeated to `<Concept n>`.
There is no table, no per-concept field list, no length guidance in the template. §7 by contrast
ships four named slots. §8 ships none.

**The one structural rule is a heading per concept, and a cap on how many.** From the template's
*Structure* block: "Pick **only** the most-needed topics for your system and assign each a level-2
heading in this section (e.g. 8.1, 8.2 etc)", immediately followed by "DO NOT ATTEMPT to cover all
of the topics of the aforementioned diagram." The website
([docs.arc42.org/section-8](https://docs.arc42.org/section-8/)) renders the second sentence as a
block quote under a heading "Structure of this section".

**arc42's own worked examples of what a concept is.** The §8 section page carries three, under
*Background*, and they are the only concrete examples arc42 publishes on either section page:

> * Within a system, a common format for log-messages shall be established, combined with a common
>   convention of choosing the appropriate log-destination. These decisions, along with
>   implementation examples, could be described as "logging-concept".
> * A system has numerous backend services, that communicate among each other based upon remote
>   procedure calls or https-based REST. … For this authentication, a central common authorization
>   service has to be used.
> * (taken from the HTML Sanity Checker, see below): All (7+) checker components within the system
>   are structured according to the strategy pattern.

All three are a rule plus its implementation, and the first two contain the words "shall be" and
"has to be" — a concept is written as an obligation, not as a report.

**The suggested concept groups.** [Tip 8-10](https://docs.arc42.org/tips/8-10/) publishes the
checklist as a three-column table (Category / Topic / Explanation) with seven bold categories:
**Domain concepts**; **User Experience concepts (UX)** (User interface, Ergonomics,
Internationalization (i18n)); **Safety and security concepts** (Security, Safety); **Architecture
and design patterns**; **"Under-the-hood" concepts** (Persistency, Process control, Transaction
handling, Session handling, Communication and integration, Exception and error handling,
Parallization and threading, Plausibility checks and validation, Business rules, Batch processing,
Reporting); **Development concepts** (Build, test, deploy; Code generation; Migration;
Configurability); and **Operational concepts** (Administration, Management, Disaster-Recovery,
Scaling, Clustering, "Monitoring, Logging", High Availability, Load balancing).

[FAQ C-8-2](https://faq.arc42.org/questions/C-8-2/) gives a seven-way grouping over overlapping but
not identical topics, and credits it: "Initially, Stefan Zörner provided the idea of sub-structuring
section 8." The two lists diverge in both directions. C-8-2's "**Under the hood**: persistence,
distribution, transactions, session-handling, caching, threading, exception and error handling,
security" adds *distribution* and *caching*, which tip 8-10 does not list; C-8-2's "**Operations**
concepts: deployment, installation, monitoring" drops all of Administration, Management,
Disaster-Recovery, Scaling, Clustering, High Availability and Load balancing.
[Tip 8-3](https://docs.arc42.org/tips/8-3/) states the size of the checklist and the intended
reaction to it: "arc42 contains a list of more than 20 proposals for recurring topics — way too many
for most real-life systems", then three steps — select what is "absolutely relevant or neccessary",
prioritise, and elaborate only the top priorities.

**On length, the guidance is "briefly".** [FAQ C-8-3](https://faq.arc42.org/questions/C-8-3/): "Work
on the highest priorities and briefly (!) document the corresponding decisions. Many crosscutting
concepts will be highly technical, therefore you document or specify those for developers. Source
code with brief explanations can sometimes be sufficient — and can save you from writing awkward
documents!" [Tip 8-1](https://docs.arc42.org/tips/8-1/) makes the economic argument: "You can often
save a lot of documentation effort by explaining concepts, instead of concentrating on building
block details."

**What a concept must contain.** [Tip 8-4](https://docs.arc42.org/tips/8-4/) — "In concepts, explain
HOW it works!": "You should document or specify concrete, real solution approaches, not abstract
theories. Explain, how these concepts are applied in reality, how they are implemented in source
code." [Tip 8-8](https://docs.arc42.org/tips/8-8/) ranks the media: unit tests first ("Unit tests
have their prerequisites (in the setup methods) and their assertions/consequences (in the assert
statements) made explicit"), then automated inclusion ("In the ideal case you include source code
directly from your code repository … That ensures your arc42 documentation always contains current,
tested and correct code"), then a reference ("If your tools don't allow for automated inclusion,
refer to relevant code instead of copy/pasting it"). It does not forbid the last resort, it
constrains it: "**Don't copy/paste!** If everything fails - and you absolutely HAVE to copy/paste
code, then restrict to the most fundamental or important parts. Don't copy extensive code fragments
manually into your documentation."

[FAQ C-8-5](https://faq.arc42.org/questions/C-8-5/), "Are there any general rules how to describe a
'concept'?", is the only page that lists per-concept rules, six of them:

1. "Be practical and use source code examples to explain and demonstrate."
2. "Write your concepts in the form of _developer use cases_\": \"A developer wants to achieve
   XYZ\" - and explain step by step what people have to do."
3. "Explain _reasons_ why the concept is like it is."
4. "You can combine text with static and dynamic diagrams to describe your more complicated
   concepts."
5. "Describe the applicability: In which or for what cases shall the concept be applied?"
6. "Describe the limits: In what cases, under which circumstances will the concept fail or cease to
   work?"

Rules 1, 3 and 4 restate what tips 8-4, 8-8 and the *Form* block already say, and rule 3 in
particular is not peculiar to §8 — [FAQ C-7-4](https://faq.arc42.org/questions/C-7-4/) carries a
section headed "Explain reasons" for §7 diagrams, and tip 7-2's per-node table has a "reason for
selection" row. Rules 2, 5 and 6 — the developer use case, applicability and limits — appear on no
other arc42 page, established by grepping the whole `_posts` and `_pages` trees of
`arc42/docs.arc42.org-site` and the whole `_posts` tree of `arc42/faq.arc42.org-site` for
`applicab`, `developer use case` and `cease to work`.

**The relationship to §4.** [docs.arc42.org/section-4](https://docs.arc42.org/section-4/) tells §4
to stay short and delegate: "Keep the explanation of these key decisions short. … Refer to details
in the following sections (section 5 for structural details, section 8 for crosscutting concepts)."
[Tip 4-4](https://docs.arc42.org/tips/4-4/) is titled "In the solution strategy, refer to concepts,
views or code!" and opens "Avoid redundancy, don't repeat information from views or concepts." So §4
is the summary and §8 is where the detail of a *concept* lives — the direction is §4 → §8.

**The relationship to §9.** [docs.arc42.org/section-9](https://docs.arc42.org/section-9/) states the
anti-redundancy rule in its most explicit words: "Please use your judgement to decide whether an
architectural decision should be documented here in this central section or whether you better
document it locally (e.g. within the white box template of one building block). **Avoid redundant
texts.** Refer to section 4, where you captured the most important decisions of your architecture
already." That exact phrase is unique to §9 — `redundant` occurs in no other `_pages` or `_posts`
file of `arc42/docs.arc42.org-site` — but the *instruction* is not: tip 4-4 gives it for §4, tip
5-10 gives it under the heading "Troublesome redundancy", and the §8 template gives it in its own
*Background* block (quoted in section 8 below). Section 6 reads it against the published examples.

Eleven tips are published under `tips/8-*` — 8-1 through 8-11, no gaps, established by listing
[`_posts/08-concepts/`](https://github.com/arc42/docs.arc42.org-site/tree/main/_posts/08-concepts).

## 3 Where the template draws the §7 / §8 line

**Operational concerns sit on both sides, and arc42 says so on both pages.**
[Tip 7-9](https://docs.arc42.org/tips/7-9/) — "Explain what (else) is relevant for productive use
(aka operation) of the system!" — puts operations squarely in §7 and enumerates it: correct
operating-system version and patches, accounts and access rights, directories, "Create and configure
databases, including required DB accounts plus access rights", "Migration of already existing
application data", middleware (web server, proxy, load balancer, directory server, message bus),
network and firewall setup, and "Setup and configuration of required security measures (i.e
certificates or other cryptographic keys, disk- or database encryption)". Its second half is a rule:
"You never want to _manually_ perform all these tasks … You should instead _thorougly_ document your
setup — at best by means of automation scripts."

Meanwhile [tip 8-10](https://docs.arc42.org/tips/8-10/)'s checklist has an **Operational concepts**
category holding Administration, Management, Disaster-Recovery, Scaling, Clustering, "Monitoring,
Logging", High Availability and Load balancing, and
[FAQ C-8-2](https://faq.arc42.org/questions/C-8-2/) lists "**Operations** concepts: deployment,
installation, monitoring" as one of the seven §8 groups. The words *deployment*, *migration* and
*monitoring* therefore appear as §7 material on one page and as §8 material on another.

**Backup is not placed at all.** The word `backup` occurs exactly once in the whole
`arc42/docs.arc42.org-site` content tree — in [tip 11-5](https://docs.arc42.org/tips/11-5/),
"Analyze data or data structures for problems and risks!": "Maybe even data distribution,
-replication, -backup or -synchronization might contain risks or problems" — that is, in §11, and as
a risk rather than as a concept. It occurs zero times in the `arc42/faq.arc42.org-site` content tree
and zero times in the English template files. The nearest §8 row is tip 8-10's "Disaster-Recovery";
C-8-2's Operations group has no backup entry. Established by grepping all three repository trees for
`backup`.

**arc42 publishes no rule that assigns an operational topic to one of the two sections** —
established by reading all ten `tips/7-*` pages, all eleven `tips/8-*` pages, both section pages and
all sixteen `faq.arc42.org` questions under sections 7, 8 and 9 (six under §7, `C-7-1` … `C-7-6`;
six under §8, `C-8-1` … `C-8-6`; four under §9, `C-9-1` … `C-9-4`, established by listing
`_posts/C-arc42/07-deployment`, `08-concepts` and
[`09-decisions`](https://github.com/arc42/faq.arc42.org-site/tree/main/_posts/C-arc42/09-decisions)),
none of which contains such a rule.

What the pages do carry is a direction of reference, and it runs both ways.

- **§7 → §8 is stated explicitly.** [FAQ C-7-6](https://faq.arc42.org/questions/C-7-6/) asks what to
  do "when my building blocks get dynamically assigned an execution environment (node) — so I cannot
  statically assign them to infrastructure nodes?" and answers: "If some part of your system or your
  infrastructure decides at runtime _where_ a particular instance of a building block gets executed,
  then the deploment view should at least explain this behavior. **It might be useful to create a
  'dynamic deployment concept' in arc42 section 8 and refer to this concept from the deployment
  view.**" It adds the modern-architecture caveat: "Some modern architecture styles (like
  microservices, self-contained systems or especially serverless-architectures) already said
  _bye-bye_ to static mapping of building blocks to specific nodes."
- **§8 → §7 is stated as influence, not as containment.** §7's motivation says the infrastructure
  "can and will influence a system and/or some cross-cutting concepts". No arc42 page says a
  cross-cutting concept may be written inside §7.

The operative distinction is therefore not topical but grammatical. §7 holds **instances**: this
node, this channel, this artifact on that machine, this environment. §8 holds **rules that hold
across building blocks**: [tip 8-1](https://docs.arc42.org/tips/8-1/) — "_Crosscutting_ means
exactly what it says: a concept is not the property of any single building block, but a decision
that several of them share. That is why it does not belong in any one building block description —
it would have to be repeated in each of them" and "A concept does not have to run through _every_
building block to be crosscutting — spanning several of them is enough."
[FAQ C-8-1](https://faq.arc42.org/questions/C-8-1/) gives the same test as a list: "Decisions, or
concepts that cannot adequatly be assigned to a single building block" and "Decisions or rules that
influence several: building blocks / parts of the implementation / runtime scenarios / interfaces /
several developers." A statement about one node is §7 whatever its topic; a rule that several nodes
obey is §8 whatever its topic.

## 4 Does §7 require a diagram, and of what kind

**No arc42 page states a diagram requirement for §7.** The word "must" does not occur anywhere on
[docs.arc42.org/section-7](https://docs.arc42.org/section-7/) or in the template file — established
by grepping both for `\bmust\b` with zero matches. The strongest wording is the *Form* block, and it
is permissive:

> * UML offers deployment diagrams to express that view. Use it, probably with nested diagrams,
>   when your infrastructure is more complex.
> * When your (hardware) stakeholders prefer other kinds of diagrams rather than a deployment
>   diagram, let them use any kind that is able to show nodes and channels of the infrastructure.

The `_**<Overview Diagram>**_` line is the first of the four level-1 slots listed in section 1, and
it is written as a fill-in placeholder in the same style as `_<explanation in text form>_`. The site
version states it in the indicative rather than the imperative — "In this section you will zoom into
this black box using additional deployment diagrams" — which is weaker than an obligation and
stronger than an option. The level-1 help asks for "a combination of diagrams, tables, and text",
which is the same reading: a diagram is expected, no page says the section is invalid without one,
and one published example (NFDI4Earth, section 5) has no deployment diagram at all.

**One diagram may carry both halves of §7.** [Tip 7-6](https://docs.arc42.org/tips/7-6/), "Use UML
deployment diagrams to document software/hardware mapping!", is one sentence and a list: "In (UML)
deployment diagrams you can show both: structure of the hardware involved in the system / mapping of
architecture building blocks to hardware." So the two-item content definition of section 1 does not
imply two artefacts.

**A table is an explicitly sanctioned substitute, not a fallback.**
[Tip 7-7](https://docs.arc42.org/tips/7-7/), "Use tables to document software/hardware mapping!!",
opens: "As a (simple) alternative to graphical mapping with deployment diagrams (see tip 7-6
(deployment diagrams)), you could use tables to document or specify deployment of software on
hardware", and shows a three-column Server / Artifact / Remark table.
[FAQ C-7-4](https://faq.arc42.org/questions/C-7-4/) goes further and asks for a table *beside* the
diagram: "The UML provides only this type of diagram for deployment and infrastructure, therefore
you have no practical alternative. On the other hand, you can of course use any free form of diagram
to depict your technical infrastructure. Make sure that stakeholders understand such notations …
Please add textual explanation (e.g. a table!) to your diagrams, where you briefly explain the
elements, their responsibility and any additional information that is required to understand the
situation." [Tip 7-1](https://docs.arc42.org/tips/7-1/) permits free-form graphics with one
condition: "In case your stakeholder like such graphical icons or symbols: use a consistent set of
such symbols with a _defined_ semantic!"

**arc42 names C4, but teaches no C4 deployment notation.** The template names UML and "any kind that
is able to show nodes and channels", and nothing else: the strings `C4 model`, `Deployment_Node` and
`Structurizr` occur zero times in the `_posts`, `_pages` and `_data` trees of
`arc42/docs.arc42.org-site`, and `\bC4\b` matches only two table cells in
[tip 9-2](https://docs.arc42.org/tips/9-2/), where `C4` is a criterion identifier in a decision
matrix. The FAQ is different. [FAQ B-17](https://faq.arc42.org/questions/B-17/), "What about arc42
and C4?", opens "Simon Browns [C4](https://c4model.com/) model is in widespread use to document
software architectures" and judges it: it "has _many_ similarities to a few sections from arc42, but
omits certain parts (e.g. quality requirements, crosscutting concepts, risks and a few others)",
then links five third-party comparisons. [FAQ D-2](https://faq.arc42.org/questions/D-2/) lists "Simon
Browns pragmatic C4 model" among modelling alternatives. And arc42's own examples index tags
geOrchestra Gateway "C4 section structure, Markdown, Structurizr diagrams" in
[`_data/in-the-wild.yml`](https://github.com/arc42/examples.arc42.org-site/blob/main/_data/in-the-wild.yml).
So the accurate statement is narrow: arc42 acknowledges C4 as a comparable model and links documents
that use it, and publishes no C4 notation of its own for §7.

That gap is open and known. [`arc42/arc42-template` issue
#228](https://github.com/arc42/arc42-template/issues/228), "Suggestion: Reference C4 Model as an
Diagramming Approach in arc42", opened 2025-11-21 and still open, asks arc42 "to acknowledge it as a
widely used and compatible approach" and offers a mapping table whose last row is "Deployment | 
Deployment | Direct match".

**Mermaid has the notation.** `C4Deployment` is one of the five C4 diagram types documented at
[mermaid.js.org/syntax/c4](https://mermaid.js.org/syntax/c4.html), with
`Deployment_Node(alias, label, ?type, ?descr, ?sprite, ?tags, $link)`, the short alias `Node()`, and
the left/right variants `Node_L()` and `Node_R()`; `Deployment_Node` blocks nest, and `Container()`
sits inside them. The page carries a standing caveat on all C4 support: "This is an experimental
diagram for now. The syntax and properties can change in future releases. Proper documentation will
be provided when the syntax is stable."

## 5 The published examples, measured

[examples.arc42.org](https://examples.arc42.org/) republishes eight complete arc42 documents — a
ninth entry, `rgcat`, is a landing page with no sections — one directory per system, one Markdown
file per section. Seven of the nine directories also carry an `_originals/` directory, but its
contents differ in kind and only three of them make the author's own §7 and §8 readable: `biking`
(38 files, the full AsciiDoc set), `doctoolchain-v4` (50 files, chapters plus an ADR register) and
`status.arc42.org` (63 files, chapters plus ADRs). `htmlsc` holds one sample file, `fin-mig`,
`mama` and `nfdi4earth` hold only non-text originals (a `.docx`, an `.xmind` and a `.graffle`, a
PDF), and `tpu` and `rgcat` hold none. That matters for section 6.2, whose argument rests on
status.arc42.org's original being available.

The republished layout makes section lengths comparable: the byte counts below are the sizes of the
hosted per-section Markdown files in
[`arc42/examples.arc42.org-site`](https://github.com/arc42/examples.arc42.org-site) at `HEAD`, read
2026-09-10. Heading counts are of level-2 headings in the same files. Three further documents are
added from arc42's own `in-the-wild.yml` list, measured in their own source: DokChess (per-section
Markdown files, summed per section), Urbo (byte ranges of one 80,575-byte Markdown file) and
geOrchestra Gateway (rendered page text, not source — its numbers are not byte-comparable with the
rest and are marked).

| Document | §7 | §8 | §9 | §8 sub-headings | §7 notation | §8 form | Decision log | How §8 cites a decision |
|---|---|---|---|---|---|---|---|---|
| [docToolchain v4](https://examples.arc42.org/systems/doctoolchain-v4/08-crosscutting-concepts/) | 1,909 B | 16,313 B | 66,631 B | 12 | PlantUML `!include <C4/C4_Deployment>` in [the original](https://github.com/arc42/examples.arc42.org-site/blob/main/_systems/doctoolchain-v4/_originals/chapters/07_deployment_view.adoc), a PNG on the hosted page; 4×4 table beside it | prose + tables + code | 20 ADRs, own files under `adrs/` | inline id in parentheses, 15 references to 5 ADRs; one "See ADR-8 for …" hand-off |
| [biking2](https://examples.arc42.org/systems/biking/08-crosscutting-concepts/) | 816 B | 13,737 B | 3,094 B | 17 | one raster image; Node/artifact × 4 table | prose + tables + one included XML file | 3 prose decisions, Problem/Alternatives/Decision | never — no §9 reference in §8 |
| [MaMa](https://examples.arc42.org/systems/mama/08-crosscutting-concepts/) | 2,957 B | 6,627 B | 855 B | 4 | one raster image; Element/Description × 4 table | prose + element tables + images; 8.2 is two `TODO` bullets | 3 decisions as a definition list | never |
| [HTML Sanity Checker](https://examples.arc42.org/systems/htmlsc/08-crosscutting-concepts/) | 3,543 B | 7,756 B | 1,684 B | 4 (6 in the project's own repo) | raster PNG exported from Enterprise Architect, footnoted "outdated"; Node/Artifact × 5 table | one file per concept, included | 3 prose decisions; only the first uses Goals/Criteria/Alternatives | never; §9 links **into** §8 |
| [Traffic Pursuit Unit](https://examples.arc42.org/systems/tpu/08-crosscutting-concepts/) | 1,880 B | 2,628 B | 1,561 B | 2 | Enterprise Architect UML deployment diagrams, plus a photograph of the rack; no table — per-node prose | 8.1 is an image + a 9-row glossary table; 8.2 is Motivation/Solution prose | 3 short decisions | never |
| [fin-mig](https://examples.arc42.org/systems/fin-mig/08-crosscutting-concepts/) | 829 B | 1,813 B | 1,917 B | 3 | one raster image, no table | prose, three paragraphs | 5 decisions in a definition list, each tagged *decided by* | never |
| [status.arc42.org](https://examples.arc42.org/systems/status.arc42.org/08-crosscutting-concepts/) | 2,823 B | 1,831 B | 26,584 B | 4 | fenced ASCII-art block; Building block / Infrastructure × 4 table | prose, one paragraph per concept | 20 Nygard ADRs, `adrs/0001-…0020-…` | never — and both sections were **empty in the original** |
| [NFDI4Earth](https://examples.arc42.org/systems/nfdi4earth/08-crosscutting-concepts/) | 10,910 B | 1,730 B | 3,756 B | 0 | no deployment diagram: prose under Infrastructure Level 1/2 with 8 tables and one schedule image | a list of links to §1, §2, §4, §5 and §7 | a 6-row decision table, no ADRs | it is nothing but pointers |
| [DokChess](https://github.com/DokChess/website_de/tree/master/content/08_konzepte) | 2,249 B | 16,004 B | 11,309 B | 7 files | a deployment diagram image on the single `7.1 Infrastruktur Windows` page | one Markdown file per concept, plus an `_index.md` | 2 long decisions, `09_entscheidungen/` | "( → Entscheidung 9.N „title" )" in 2 of 7 concepts |
| [Urbo](https://gitlab.opencode.de/stadt-soest/city-app/soest-city-app/-/blob/main/docs/architecture/arc42.md) | 5,770 B | 6,259 B | 10,679 B | 9 | Mermaid `graph LR` flowchart, no table | prose + bullet lists, one `##` per concept | 11 ADRs, `ADR-001`…`ADR-011`, inline in §9 | never — zero `ADR-\d+` matches in §8 |
| [geOrchestra Gateway](https://docs.georchestra.org/gateway/en/latest/arc42/crosscutting/) | 7,933 B* | 6,896 B* | none | 13 (10 named concepts) | Mermaid diagram; sub-headings include "Hardware Requirements", "Scaling Strategies", "Monitoring and Operations" | prose per concept, plus Overview / Implementation / Best Practices | none — `sections: All but 4 and 9` | there is no §9 to cite |

`*` rendered page text, not source bytes.

Six observations the table makes mechanically.

- **§8 is normally the longer of the two.** In eight of eleven documents §8 exceeds §7, by a factor
  between 1.1 (Urbo) and 16.8 (biking2). The three exceptions are NFDI4Earth (§7 is 6.3× §8),
  status.arc42.org (§7 is 1.5× §8) and geOrchestra Gateway (§7 is 1.2× §8) — two of them documents
  whose §8 is not really written.
- **The concept count clusters low.** Excluding NFDI4Earth's zero, the median is 7 sub-headings and
  the range is 2 to 17. No example covers tip 8-10's checklist in full; biking2's 17 comes closest
  to tip 8-3's "more than 20 proposals for recurring topics", within about 15% of it.
- **A concept is a prose section in every document; no document encodes a concept as a row of a
  concepts table or as a bare link, except NFDI4Earth.** Where a table appears inside §8 it carries
  a glossary or an element inventory. TPU's §8.1 is the edge case: an image plus a nine-row glossary
  table and no prose at all, so there the table *is* the concept. Thin or unwritten concepts appear
  in three documents — NFDI4Earth (zero headings), MaMa (§8.2 is two `TODO` bullets and §8.4.1 is an
  empty heading) and status.arc42.org (the original was the untouched placeholder).
- **§7 stays small.** Seven of the eight hosted documents are under 3.6 KB. The outlier is
  NFDI4Earth at 10,910 B, a federated research infrastructure with per-service VM and certificate
  detail; among the added documents, geOrchestra Gateway and Urbo are the next largest.
- **Every notation appears at least once and none dominates.** Raster images (biking2, MaMa,
  fin-mig, HSC, DokChess), UML deployment diagrams from a modelling tool (TPU, HSC), C4 PlantUML
  (docToolchain v4), Mermaid (Urbo, geOrchestra), fenced ASCII art (status.arc42.org) and no diagram
  at all (NFDI4Earth). Six of the eleven put a node inventory table beside the picture.
- **Keeping a decision log does not predict citing one.** Four documents keep a numbered register
  (docToolchain v4, status.arc42.org, Urbo, DokChess). Two of them cite it from §8 and two never do.

## 6 §8 next to a decision log

This is the load-bearing question for #40, so it is answered per document, from the source.

### 6.1 docToolchain v4 — a concept cites an ADR by id and never repeats it

docToolchain v4 keeps eighteen numbered ADRs plus two proposed ones (`adr-tbd-1`, `adr-tbd-2`) as
separate AsciiDoc files under `src/docs/arc42/adrs/`, and its
[§9](https://examples.arc42.org/systems/doctoolchain-v4/09-architecture-decisions/) is an index — a
three-column table of ADR number, title and Nygard status ("Proposed / Accepted / Superseded /
Deprecated"), followed by twenty `include::` lines. §9 also states where the boundary is: "The ADRs
themselves live in the register at `src/docs/arc42/adrs/` and are included below."

Its §8 nonetheless runs 16,313 B over twelve concepts: Threat Model (STRIDE), Security, Test,
Observability, Error Handling, Configuration Management, Script Execution Model, Authentication
Mechanisms, Headless / CI Mode, LLM Integration Architecture, Content Transformation Pipeline and
Custom Site Generator. It references ADRs **fifteen times across five distinct records** — ADR-8
five times, ADR-11 four times, and ADR-6, ADR-7 and ADR-9 twice each (counted over the hosted
section file). Every one of them is a parenthetical identifier attached to a statement of mechanism,
never a restatement of the decision:

> Error handling is governed by ADR-8 (Actionable Error Guidance). Every user-recoverable error is
> thrown as a `DtcException` (or `DtcConfigException` / `DtcApiException`) carrying a mandatory
> `guidance` field … See ADR-8 for the exception hierarchy, exit-code table, and the runtime error
> scenario in the Runtime View section.

That is the whole pattern in three moves: **name the ADR, state what the code does now, hand the
detail back**. The same shape appears as a bare tag inside table cells — "Pinned versions (ADR-6)
reduce the window for a swapped artifact", "CodeNarc static analysis (ADR-11) sits alongside the
pyramid as a non-execution gate", "the intended control … (ADR-9, QS-16) does **not exist yet**
(R-007)".

The pointer is bidirectional. [ADR-8's own
file](https://github.com/arc42/examples.arc42.org-site/blob/main/_systems/doctoolchain-v4/_originals/adrs/adr-08-actionable-error-guidance.adoc)
ends its status paragraph with "… and `DtcRestClient` redacts its own HTTP error output via the same
logic (Chapter 8)."

What §8 owns that no ADR does, in this document, is the **grid**: a six-row STRIDE threat table with
stable ids `T-001`…`T-006` and an "Affected Building Block (Ch5)" column, then a mitigation table
whose third column is "Closes" and holds those ids. That is a many-to-many mapping across building
blocks — precisely the artefact that "would have to be repeated in each of them"
([tip 8-1](https://docs.arc42.org/tips/8-1/)) if it were not central, and precisely the artefact a
per-decision record cannot hold.

### 6.2 status.arc42.org — the decision log emptied §8, and that was recorded as a defect

status.arc42.org keeps twenty Nygard ADRs as separate Markdown files, `0001-record-architecture-
decisions.md` through `0020-use-make-for-build-test-and-deployment.md`. Its
[§9 source](https://github.com/arc42/examples.arc42.org-site/blob/main/_systems/status.arc42.org/_originals/arc42/chapters/09_architecture_decisions.adoc)
is four lines of AsciiDoc whose only content is `include::{projectRootDir}/build/adrInclude.adoc[]`
— a generated include of the entire register, which renders as 26,584 B.

Its own §8 and §7 are the **unmodified arc42 placeholder**. The §8 source file is 377 bytes and its
body is `=== _<Concept 1>_` / `_<explanation>_` … `=== _<Concept n>_`; the §7 source is 732 bytes of
`_**<Overview Diagram>**_`, `Motivation::`, `Quality and/or Performance Features::` and
`Mapping of Building Blocks to Infrastructure::`, all still empty. This is the pure case: a project
that keeps a full decision log and wrote no §7 and no §8 at all.

The arc42 examples editors did not accept that as a valid state. They wrote both sections for the
hosted version and opened each with a note saying why:

> This chapter was still an empty template in the original documentation. The concepts below are the
> ones that recur across status.arc42.org's building blocks, each originally documented as its own
> architecture decision record.

> This chapter was still an empty template in the original documentation; deployment is instead
> documented through architecture decision records. This section pulls that material together.

The repaired §8 is four concepts — Logging, Caching and rate limiting, Secrets, Number formatting —
one paragraph each, each written as a rule plus its reason: "A single global `zerolog` logger,
imported by every package. Chosen after plain `fmt.Print*` calls turned out not to work properly
once the service ran inside Fly.io's cloud runtime." Notably the repair **carries no link back to
the ADR it was distilled from** — the rendering is standalone prose. The repaired §7 is a mapping
table of four rows plus Motivation and Quality paragraphs, likewise distilled from the ADRs.

### 6.3 Urbo — a full §8 and a full ADR register that never meet

Urbo is the counter-example the other documents do not supply: a production system whose §8 is
written out over nine named concepts (8.1 Authentication and Authorization, 8.2 Domain Model, 8.3
Feature + Adapter Pattern (Frontends), 8.4 Database Migrations, 8.5 Internationalization (i18n), 8.6
Observability, 8.7 Search Indexing, 8.8 Image Processing, 8.9 Notifications) and whose §9 holds
eleven ADRs (`ADR-001` Use of Kubernetes for Deployment … `ADR-011` Casbin for Fine-Grained Resource
Authorization). A regular-expression count of `ADR-\d+` over the §8 byte range returns **zero
matches**, and a case-insensitive search of the same range for `adr`, `decision`, `section 9` and
`architecture decision` also returns zero. The reverse direction is empty too: §9 mentions
`concept` once, and never as a pointer.

The consequence is visible duplication. §8.1 explains the Casbin authorisation model in its own
words — "Permissions are expressed as `(subject, domain, object, action)` tuples", "**Tenant
isolation** — every permission is scoped to a `tenant:{name}` domain", "**Three verbs** — `read`,
`write` (covers update and delete), and `create` (POST-only)" — and `ADR-011` explains the same
model again, in the same words, under **Decision:** "Permissions are expressed as `(subject, domain,
object, action)` tuples, where the domain is always a tenant (`tenant:{name}`) …". The same subject
is written twice, 8 KB apart, with no cross-reference in either direction. This is exactly the state
[`documentation-style.md`](../documentation-style.md) §6 forbids, occurring in a document that is
otherwise complete.

### 6.4 DokChess — the one-clause hand-off, in both directions

DokChess is the document arc42's own list calls "what a finished (and polished) arc42 documentation
looks like"
([`_data/in-the-wild.yml`](https://github.com/arc42/examples.arc42.org-site/blob/main/_data/in-the-wild.yml),
kind `Invented subject`, `sections: All 12`, licence `CC BY-NC-SA`, "German, with an English
translation"). It is published as source at
[`DokChess/website_de`](https://github.com/DokChess/website_de/tree/master/content), one Markdown
file per subsection.

Its §9 holds two decisions, both long (`01_Anbindung.md` 4,280 B, `02_stellungsobjekte.md` 6,653 B)
and both written as a question — "9.1 Wie kommuniziert die Engine mit der Außenwelt?", "9.2 Sind
Stellungsobjekte veränderlich oder nicht?" — under the heading "Zur Fragestellung". Its §8 holds
seven concepts (8.1 Abhängigkeiten, 8.2 Domänenmodell, 8.3 Benutzungsoberfläche, 8.4 Validierung,
8.5 Fehlerbehandlung, 8.6 Protokollierung, 8.7 Testbarkeit) totalling 15,610 B of concept files.

Two of the seven cite a decision, and both do it in the same shape — a statement of the current
mechanism, then a parenthetical arrow to the record, and nothing else:

> Die Klasse Stellung ist ebenfalls unveränderlich, die Methode `fuehreZugAus()` liefert eine neue
> Stellung mit der veränderten Spielsituation zurück ( → Entscheidung 9.2 „Sind Stellungsobjekte
> veränderlich oder nicht?").
> ([8.2 Domänenmodell](https://www.dokchess.de/08_konzepte/02_domaenenmodell/))

> DokChess verfügt selbst über keine grafische Oberfläche, sondern agiert über das XBoard-Protokoll
> mit der Außenwelt ( → Entscheidung 9.1 ).
> ([8.3 Benutzungsoberfläche](https://www.dokchess.de/08_konzepte/03_benutzungsoberflaeche/))

§7 uses the identical device. Its single subsection, [7.1 Infrastruktur
Windows](https://www.dokchess.de/07_verteilungssicht/01_infrastruktur_windows/), reads "Als Frontend
wird exemplarisch Arena verwendet ( → Entscheidung 9.1 „Wie kommuniziert die Engine mit der
Außenwelt?")." — an instance statement in §7 handing its rationale to §9 in one clause. This is the
same pattern docToolchain v4 uses with `ADR-8`, arrived at independently, in a different language,
in a different tool chain.

### 6.5 NFDI4Earth — the only §8 that is a pure index of links

NFDI4Earth's [§8](https://examples.arc42.org/systems/nfdi4earth/08-crosscutting-concepts/) is 1,730
B with zero sub-headings. It opens "Not written yet, but scoped.", quotes the project's own online
documentation naming four planned concepts (Developer's guide, Certificate strategy, CI/CD
implementation, Identity management), then lists five concepts that already exist elsewhere in the
document as bullets, each a bold name followed by a cross-reference. Three of the five carry a
hyperlink — "**Metadata as RDF, served over a SPARQL API** … [section 5]", "**FAIR principles and
Openness** — the mission in [section 1] and constraint 7 in [section 2]", "**One service per VM,
everything in Docker, deployed by Ansible** — the operational conventions in [section 7]" — and two
are plain-text references with no link: "**Loose coupling over well-defined interfaces**, so that
any single service can be replaced — constraint 12." and "**Free and Open Source Software and open
standards** for every component — constraints 9 and 10."

So a §8 that is nothing but pointers does exist in a published arc42 document, and it is annotated
in
its first four words as unfinished.

### 6.6 HTML Sanity Checker — the link runs the other way

HSC's [§9](https://github.com/aim42/htmlSanityCheck/blob/main/src/docs/arc42/chapters/chap-09-Decisions.adoc)
is not a set of ADRs but three prose decisions, and only the first of the three is structured:
"HTML Parsing with jsoup" carries `Goals of this decision::`, `Decision Criteria::` and
`Alternatives::` labelled lists, while "String Similarity Checking with Jaro-Winkler-Distance" and
"Changing Groovy to Plain Java" are one unstructured paragraph each. The jsoup decision ends: "Find
details on how HSC implements HTML parsing in the {xrefConceptHtmlEncapsulation}." — the decision
points into §8, and the §8 concept it points at is 338 bytes, three lines of prose. HSC therefore
splits the same subject the other way round from docToolchain: §9 keeps the alternatives and the
criteria, §8 keeps one sentence of mechanism, and neither repeats the other.

### 6.7 Was a thin §8 ever recorded as a problem?

Yes, once, by the arc42 editors themselves, in the two hosted repair notes quoted in 6.2, and once
more in NFDI4Earth's own "Not written yet, but scoped." No arc42 issue tracker records it. The
issue lists of `arc42/arc42-template` (100 most recent issues and pull requests), of
`arc42/docs.arc42.org-site` (100 most recent) and of `arc42/examples.arc42.org-site` (all four,
every one a pull request) were read in full through the REST issues endpoint with `state=all`, and
none reports an empty, thin or link-only §8 as a defect. The closest entries are
[`docs.arc42.org-site` #74](https://github.com/arc42/docs.arc42.org-site/issues/74), "more extensive
explanation of concepts", [#82](https://github.com/arc42/docs.arc42.org-site/issues/82), "add tip to
use stereotypes or short ids to refer to concepts" — the request that became tip 8-11 — and
[`arc42-template` #154](https://github.com/arc42/arc42-template/issues/154), "Cross-cutting concepts
vs cross-cutting concerns". **[unverified beyond that — the three lists are capped at the 100 most
recent items each and the endpoint mixes issues with pull requests, so an older issue could exist;
GitHub's search endpoint, which would settle it, returns `401 Unauthorized` unauthenticated in this
environment.]**

### 6.8 The rule arc42 itself publishes for this

[Tip 8-9](https://docs.arc42.org/tips/8-9/) is titled "Document decisions instead of concepts!" and
is short enough to quote whole:

> You can interpret concepts as special cases of architecture and/or design decisions (see arc42
> section 9).
>
> ```
> if (extensive-explanation-required)
>    then concept
>    else decision
> ```
>
> Even from a decision (in arc42 section 9) you can refer (or hyperlink) to the corresponding source
> code (or even better, appropriate unit tests!). That's sometimes sufficient for developers…

That is arc42's own answer, and it is a test on *explanation length*, not on subject. A topic that
can be settled by "we chose X because Y, and here are the consequences" is an ADR and needs no §8
entry. A topic that needs to be shown — mechanism, applicability, limits, the grid of which building
blocks obey it, the code — earns a concept.

Two more pages complete the mechanism. [Tip 8-11](https://docs.arc42.org/tips/8-11/), "(Hyper)Link
between Building Blocks and Concepts!", opens with the rule — "You should denote which concepts are
applied in certain building blocks." — then asks for concepts to be *named* and the names used as
stereotypes on building blocks: "Assign a unique name to important concepts … Intention-revealing
names would be perfect", with «fyne-ui» and «template-method-pattern» as worked examples. Its third
heading, "Building blocks might apply several concepts", makes the mapping many-to-many: "A building
block might have a graphical user interface (and implement the «our-special-GUI»), and at the same
time store its persistent data in a schema-free noSQL database, following your
«schema-free-persistence» concept." [Tip 5-10](https://docs.arc42.org/tips/5-10/) is its counterpart
in §5: "instead of repeating recurring building-block substructures, factor those out into a
crosscutting concepts", so that blocks carry the stereotype «X-service» "refering to a crosscutting
concept that explains how elements of type X-service» shall be constructed, build or implemented."

**So what is left as §8's own content when every decision is an ADR?** Mechanically, from the pages
and the examples above, four things, and nothing else:

1. **The mechanism as it exists now** — how the rule is implemented, with references into code or
   tests (tips 8-4, 8-8; docToolchain's Error Handling paragraph; DokChess's 8.3 sentence;
   status.arc42.org's repaired Logging paragraph).
2. **The grid** — which building blocks the rule applies to, and the names that mark them (tips 8-1,
   8-11, 5-10; docToolchain's `T-NNN` threat/mitigation matrix).
3. **Applicability and limits** — "In which or for what cases shall the concept be applied?" and "In
   what cases … will the concept fail or cease to work?"
   ([FAQ C-8-5](https://faq.arc42.org/questions/C-8-5/)); docToolchain's "Trust model and accepted
   risks" sub-section is exactly this.
4. **The domain model**, which no decision record holds — tips
   [8-5](https://docs.arc42.org/tips/8-5/), [8-6](https://docs.arc42.org/tips/8-6/) and
   [8-7](https://docs.arc42.org/tips/8-7/) put "business or domain models or elements" in §8 and
   defer the term definitions to §12; five of the measured documents open §8 with one (biking2, TPU,
   HSC, MaMa, DokChess), and Urbo keeps one as §8.2.

What an ADR keeps and §8 must not repeat is the Nygard payload:
[FAQ C-9-3](https://faq.arc42.org/questions/C-9-3/) lists it as Title, Context ("Forces at play,
including technological, political, social, and project organizational"), Decision, Status and
Consequences. §9's page states the anti-duplication rule directly: "Avoid redundant texts."

## 7 The concept-per-file shape

**arc42 does not recommend splitting §8 into separate documents.** None of the eleven `tips/8-*`
pages mentions files, directories or splitting — established by reading all eleven and by grepping
`_posts/08-concepts/` for `file`, `directory` and `split`. The only structural instruction is the
template's: "assign each a level-2 heading in this section (e.g. 8.1, 8.2 etc)", i.e. one section
with sub-headings. What the *Form* block permits — "concept papers with any kind of structure" — is
the closest the template comes, and it is about the internal structure of a concept, not about where
it is stored. [Tip 8-8](https://docs.arc42.org/tips/8-8/) does ask for inclusion machinery, but for
*source code*: "In the ideal case you include source code directly from your code repository."

The examples split practice cleanly in two:

- **One file, sub-headings.** docToolchain v4 keeps all twelve concepts in a single 16,528-byte
  `08_concepts.adoc`. biking2 keeps seventeen in one file. Urbo keeps nine inside one 80,575-byte
  document that holds all twelve sections. Every document republished on examples.arc42.org is one
  file per section by construction.
- **A directory, one file per concept.** HTML Sanity Checker's
  [`chap-08-Concepts.adoc`](https://github.com/aim42/htmlSanityCheck/blob/main/src/docs/arc42/chapters/chap-08-Concepts.adoc)
  is 3,660 bytes: five `include::` lines — `chap-08-checking-domain.adoc` (2,507 B),
  `chap-08-gradle-plugin.adoc` (1,927 B), `chap-08-maven-plugin.adoc` (897 B),
  `chap-08-checking-algorithms.adoc` (4,912 B), `chap-08-html-encapsulation.adoc` (338 B) — and then
  a sixth concept, "Flexible Reporting", written inline in the spine itself. The concept files are
  ordinary `=== Heading` fragments carrying their own anchor (`[[checking-concept]]`,
  `[[sec:html-encapsulation]]`), so the split is invisible in the rendered document.
  DokChess does the same with a static-site generator instead of an include chain:
  [`content/08_konzepte/`](https://github.com/DokChess/website_de/tree/master/content/08_konzepte)
  holds an `_index.md` of 394 B carrying the section's two-sentence introduction, then seven concept
  files of 1,704–2,878 B, each rendered as its own page under `/08_konzepte/`. §7 and §9 use the
  identical layout.

The HSC layout shows the cost and the benefit together: the smallest concept is 338 bytes, three
lines of prose in a file of its own, and the largest is 4,912 bytes with seven `====` sub-headings
(`MissingImageFilesChecker`, `MissingImgAltAttributeChecker`, `BrokenCrossReferencesChecker`,
`DuplicateIdChecker`, `MissingLocalResourcesChecker`, `BrokenHttpLinksChecker`,
`IllegalLinkChecker`, plus one deeper `===== Current limitations:`) — a range of 15× that a single
file would have flattened into an uneven set of sibling sections. DokChess's range is 1.7×, which is
what a directory looks like when the concepts are of a size.

## 8 What the two pages forbid

Statements of the form "this does not belong here", collected from both sections:

- **§8: do not work the checklist.** "Pick **only** the most-needed topics for your system" and "DO
  NOT ATTEMPT to cover all of the topics of the aforementioned diagram" (template §8).
  [Tip 8-3](https://docs.arc42.org/tips/8-3/) is titled "Restrict documentation of concepts to the
  most important topics!"; [FAQ C-8-3](https://faq.arc42.org/questions/C-8-3/) turns it into an
  instruction: "Remove every topic that is not relevant for your system"; and
  [C-8-2](https://faq.arc42.org/questions/C-8-2/) repeats it with an exclamation mark: "You shall
  remove (!) all concepts not relevant for your system."
- **§8: do not repeat a concept inside the building blocks it governs.** "It might be easier to
  communicate or document such _cross-cutting_ topics at a central location, instead of repeating
  them in the description of the concerned building blocks, hardware elements or development
  processes" (template §8, *Background*). Tip 8-1 states the converse — a concept "does not belong
  in any one building block description".
- **§8: do not paste code.** "**Don't copy/paste!** … Don't copy extensive code fragments manually
  into your documentation" ([tip 8-8](https://docs.arc42.org/tips/8-8/)) — a restriction on the
  fallback, not a ban: "If everything fails - and you absolutely HAVE to copy/paste code, then
  restrict to the most fundamental or important parts."
- **§8: do not write theory.** "You should document or specify concrete, real solution approaches,
  not abstract theories" ([tip 8-4](https://docs.arc42.org/tips/8-4/)).
- **§7: do not document infrastructure past what the deployment needs.** "From a software
  perspective it is sufficient to capture only those elements of an infrastructure that are needed
  to show a deployment of your building blocks" (template §7), and "Include only such information in
  the software architecture documentation that's neccessary to understand the associated
  architecture decisions" ([tip 7-10](https://docs.arc42.org/tips/7-10/)).
- **§4 and §9: do not restate.** "Avoid redundancy, don't repeat information from views or concepts"
  ([tip 4-4](https://docs.arc42.org/tips/4-4/)) and "Avoid redundant texts"
  ([docs.arc42.org/section-9](https://docs.arc42.org/section-9/)).

**§8 is where rules and implementation restrictions belong, and arc42 says so twice.**
[Tip 5-10](https://docs.arc42.org/tips/5-10/) carries the sentence as a block quote: "Crosscutting
concepts might describe principles, rules or implementation restrictions that must hold for specific
kinds of building blocks. See [section 8](https://docs.arc42.org/section-8/) for details." And
[tip 8-2](https://docs.arc42.org/tips/8-2/) lists "regulations" and "rules" among the nine names
practitioners give to §8 entries. So the answer to sub-question 8 is that arc42 invites a rule into
§8 explicitly, provided the rule holds across building blocks.

What arc42 never uses is the vocabulary of a style guide. The phrases `coding guidelines`, `coding
standard`, `coding convention` and `style guide` occur zero times in the `_posts` and `_pages` trees
of `arc42/docs.arc42.org-site`, tip 8-10's **Development concepts** category has no coding-standards
row — it is only "Build, test, deploy", "Code generation", "Migration" and "Configurability" — and
[FAQ C-8-2](https://faq.arc42.org/questions/C-8-2/)'s Development group is "Build and build
management, code generation, configuration, (automated) testing, migration". arc42 places the rule
in §8 and stays silent on where a *formatting* rule goes. Established by grepping the downloaded
repository tree in full; the tree is the site's whole content, so the negative holds for the
rendered site as well.

## 9 What the evidence supports

- **A deployment view carried by a table plus a container-shaped diagram is inside the template.**
  The *Form* block asks only for "any kind that is able to show nodes and channels of the
  infrastructure"; [tip 7-7](https://docs.arc42.org/tips/7-7/) offers a table as an explicit
  alternative to a diagram; [tip 7-6](https://docs.arc42.org/tips/7-6/) says one deployment diagram
  may carry both the hardware structure and the mapping; [FAQ C-7-4](https://faq.arc42.org/questions/C-7-4/)
  asks for a table *beside* whatever is drawn. Six of the eleven examples carry a node inventory
  table under the picture, one (NFDI4Earth) carries no deployment diagram at all, and only two (TPU
  and HSC) draw a UML deployment diagram — TPU says so in prose, HSC's is an unlabelled Enterprise
  Architect export footnoted as outdated. The notation obligation is a legend obligation: a
  consistent symbol set with "a _defined_ semantic" (tip 7-1).
- **`C4Deployment` is available and used, and arc42 neither teaches nor forbids it.** Mermaid
  documents it with `Deployment_Node`, `Node`, `Node_L`, `Node_R` and nested `Container`, under a
  standing experimental warning; docToolchain v4's own arc42 §7 is a C4 PlantUML deployment diagram
  in its AsciiDoc source. arc42 names C4 only in the FAQ (B-17, D-2) and in its examples index, and
  an open template issue (#228) asks it to say more. This repository's `docs/design/diagrams.md`
  lists six Mermaid diagram kinds and omits `C4Deployment`, which is a gap in the rulebook rather
  than a constraint from arc42.
- **§7 has four named slots, none of them mandatory, and §8 has none.** Level 1 is Overview diagram,
  Motivation, Quality and/or Performance features, Mapping; the site marks the third "(optional)"
  and the word `must` appears nowhere in either publication. Level 2 repeats level 1 for selected
  elements only and ships `_<Infrastructure Element n>_` subsections that tip 7-8 tells the author
  to use for nodes of "high importance or special meaning". §8's entire structural rule is one
  level-2 heading per concept, with the form left open.
- **The §7/§8 line is grammatical, not topical.** *deployment*, *migration* and *monitoring* appear
  on both sides of the split in arc42's own pages; *backup* appears on neither, occurring once in
  the whole documentation site and there as a §11 risk. §7 holds statements about instances — this
  node, this channel, this artifact, this environment. §8 holds rules several building blocks share,
  including "principles, rules or implementation restrictions" (tip 5-10). Where a deployment fact
  is itself a rule, [FAQ C-7-6](https://faq.arc42.org/questions/C-7-6/) says to write it as a
  concept in §8 and refer to it from §7.
- **A decision log does not discharge §8, and one published project proved it by trying.**
  status.arc42.org keeps twenty ADRs and left §7 and §8 as untouched placeholders; the arc42
  examples editors wrote both sections themselves and labelled the omission in the first sentence of
  each. NFDI4Earth, whose §8 is nothing but pointers, is labelled "Not written yet". Every other
  example with a real §8 writes each concept as prose.
- **The failure mode #40 must avoid also occurs in the other direction, and Urbo shows it.** A
  complete nine-concept §8 and a complete eleven-ADR §9 can coexist with zero cross-references and
  duplicate the same 8 KB of mechanism twice. Cross-referencing is a discipline, not a by-product of
  keeping both sections.
- **The working pattern where both exist is: name the record, state the mechanism, hand the detail
  back.** docToolchain v4 references five ADRs fifteen times inside §8 and never restates one; the
  longest form is "Error handling is governed by ADR-8 (Actionable Error Guidance). … See ADR-8 for
  the exception hierarchy, exit-code table, and the runtime error scenario." DokChess arrives at the
  same device independently — "( → Entscheidung 9.2 „Sind Stellungsobjekte veränderlich oder
  nicht?")" — and uses it from §7 as well as from §8. HSC runs the pointer the other way, from §9
  into a three-line §8 concept. This is the practice
  [`documentation-style.md`](../documentation-style.md) §6 already allows — "An arc42 section or the
  tracker may summarise a decision in one sentence next to its link."
- **arc42's own test for whether a concept survives is explanation length, not subject.**
  [Tip 8-9](https://docs.arc42.org/tips/8-9/): `if (extensive-explanation-required) then concept
  else decision`. What needs extensive explanation is the mechanism, the grid of which blocks obey
  the rule, the applicability and the limits, and the domain model. What does not is the
  alternatives and the rationale — those are the ADR's Context and Consequences, and §9 says
  "Avoid redundant texts".
- **Splitting §8 into a file per concept is unrecommended but practised, including by the document
  arc42 calls polished.** No arc42 tip mentions splitting; HTML Sanity Checker does it with an
  include spine that pulls five concept files and writes a sixth inline, and DokChess does it with a
  directory of seven concept pages plus an `_index.md`. In both, the split is invisible after
  rendering. The median measured document keeps 7 concepts, the largest keeps 17, and the
  single-file and directory layouts are about equally represented.

## Sources

arc42 template, in source form:

- <https://github.com/arc42/arc42-template/blob/master/EN/adoc/07_deployment_view.adoc> · <https://github.com/arc42/arc42-template/blob/master/EN/adoc/08_concepts.adoc> · <https://github.com/arc42/arc42-template/blob/master/EN/adoc/09_architecture_decisions.adoc>
- <https://github.com/arc42/arc42-template> (repository tree at `master`, 758 entries, listed in full: it ships the empty template in twelve languages and no filled-in example content — zero paths match `example`)
- <https://github.com/arc42/arc42-template/issues/228> · <https://github.com/arc42/arc42-template/issues/154>

arc42 documentation site (`docs.arc42.org`), pages and tips:

- <https://docs.arc42.org/section-4/> · <https://docs.arc42.org/section-7/> · <https://docs.arc42.org/section-8/> · <https://docs.arc42.org/section-9/>
- <https://docs.arc42.org/tips/7-1/> · <https://docs.arc42.org/tips/7-2/> · <https://docs.arc42.org/tips/7-3/> · <https://docs.arc42.org/tips/7-4/> · <https://docs.arc42.org/tips/7-5/> · <https://docs.arc42.org/tips/7-6/> · <https://docs.arc42.org/tips/7-7/> · <https://docs.arc42.org/tips/7-8/> · <https://docs.arc42.org/tips/7-9/> · <https://docs.arc42.org/tips/7-10/>
- <https://docs.arc42.org/tips/8-1/> · <https://docs.arc42.org/tips/8-2/> · <https://docs.arc42.org/tips/8-3/> · <https://docs.arc42.org/tips/8-4/> · <https://docs.arc42.org/tips/8-5/> · <https://docs.arc42.org/tips/8-6/> · <https://docs.arc42.org/tips/8-7/> · <https://docs.arc42.org/tips/8-8/> · <https://docs.arc42.org/tips/8-9/> · <https://docs.arc42.org/tips/8-10/> · <https://docs.arc42.org/tips/8-11/>
- <https://docs.arc42.org/tips/4-4/> · <https://docs.arc42.org/tips/5-10/> · <https://docs.arc42.org/tips/9-2/> · <https://docs.arc42.org/tips/11-5/>
- <https://github.com/arc42/docs.arc42.org-site> (site source; `_pages/section-*.md`, `_posts/07-deployment/`, `_posts/08-concepts/`, `_data/` — downloaded at `HEAD` and grepped in full for the negatives in sections 2, 3, 4 and 8)
- <https://github.com/arc42/docs.arc42.org-site/issues/74> · <https://github.com/arc42/docs.arc42.org-site/issues/82>

arc42 FAQ (`faq.arc42.org`):

- <https://faq.arc42.org/questions/C-7-1/> · <https://faq.arc42.org/questions/C-7-2/> · <https://faq.arc42.org/questions/C-7-3/> · <https://faq.arc42.org/questions/C-7-4/> · <https://faq.arc42.org/questions/C-7-5/> · <https://faq.arc42.org/questions/C-7-6/>
- <https://faq.arc42.org/questions/C-8-1/> · <https://faq.arc42.org/questions/C-8-2/> · <https://faq.arc42.org/questions/C-8-3/> · <https://faq.arc42.org/questions/C-8-4/> · <https://faq.arc42.org/questions/C-8-5/> · <https://faq.arc42.org/questions/C-8-6/>
- <https://faq.arc42.org/questions/C-9-1/> · <https://faq.arc42.org/questions/C-9-2/> · <https://faq.arc42.org/questions/C-9-3/> · <https://faq.arc42.org/questions/C-9-4/>
- <https://faq.arc42.org/questions/B-17/> · <https://faq.arc42.org/questions/D-2/>
- <https://github.com/arc42/faq.arc42.org-site> (site source; `_posts/C-arc42/07-deployment/`, `08-concepts/`, `09-decisions/` — six, six and four questions respectively)

Published arc42 documents:

- <https://examples.arc42.org/> · <https://github.com/arc42/examples.arc42.org-site> (per-system sources under `_systems/`, authors' originals under `_systems/*/_originals/` where present, external list in `_data/in-the-wild.yml`)
- <https://examples.arc42.org/systems/doctoolchain-v4/07-deployment-view/> · <https://examples.arc42.org/systems/doctoolchain-v4/08-crosscutting-concepts/> · <https://examples.arc42.org/systems/doctoolchain-v4/09-architecture-decisions/> · <https://github.com/arc42/examples.arc42.org-site/blob/main/_systems/doctoolchain-v4/_originals/chapters/07_deployment_view.adoc>
- <https://examples.arc42.org/systems/status.arc42.org/07-deployment-view/> · <https://examples.arc42.org/systems/status.arc42.org/08-crosscutting-concepts/> · <https://examples.arc42.org/systems/status.arc42.org/09-architecture-decisions/>
- <https://examples.arc42.org/systems/biking/07-deployment-view/> · <https://examples.arc42.org/systems/biking/08-crosscutting-concepts/> · <https://examples.arc42.org/systems/mama/07-deployment-view/> · <https://examples.arc42.org/systems/mama/08-crosscutting-concepts/>
- <https://examples.arc42.org/systems/tpu/07-deployment-view/> · <https://examples.arc42.org/systems/tpu/08-crosscutting-concepts/> · <https://examples.arc42.org/systems/fin-mig/07-deployment-view/> · <https://examples.arc42.org/systems/fin-mig/08-crosscutting-concepts/> · <https://examples.arc42.org/systems/fin-mig/09-architecture-decisions/>
- <https://examples.arc42.org/systems/nfdi4earth/07-deployment-view/> · <https://examples.arc42.org/systems/nfdi4earth/08-crosscutting-concepts/> · <https://examples.arc42.org/systems/nfdi4earth/09-architecture-decisions/>
- <https://github.com/aim42/htmlSanityCheck/blob/main/src/docs/arc42/hsc_arc42.adoc> · <https://github.com/aim42/htmlSanityCheck/blob/main/src/docs/arc42/chapters/chap-07-Deployment.adoc> · <https://github.com/aim42/htmlSanityCheck/blob/main/src/docs/arc42/chapters/chap-08-Concepts.adoc> · <https://github.com/aim42/htmlSanityCheck/blob/main/src/docs/arc42/chapters/chap-08-checking-algorithms.adoc> · <https://github.com/aim42/htmlSanityCheck/blob/main/src/docs/arc42/chapters/chap-08-html-encapsulation.adoc> · <https://github.com/aim42/htmlSanityCheck/blob/main/src/docs/arc42/chapters/chap-09-Decisions.adoc>
- <https://www.dokchess.de/07_verteilungssicht/> · <https://www.dokchess.de/08_konzepte/> · <https://www.dokchess.de/09_entscheidungen/> · <https://github.com/DokChess/website_de/tree/master/content>
- <https://gitlab.opencode.de/stadt-soest/city-app/soest-city-app/-/blob/main/docs/architecture/arc42.md> (Urbo — Smart City Platform)
- <https://docs.georchestra.org/gateway/en/latest/arc42/> · <https://docs.georchestra.org/gateway/en/latest/arc42/crosscutting/> · <https://docs.georchestra.org/gateway/en/latest/arc42/deployment_view/>
- <https://github.com/bitsmuggler/arc42-c4-software-architecture-documentation-example/blob/master/documentation/arc42/07_deployment_view.adoc> (the arc42 + C4 example FAQ B-17 links to: a C4 PlantUML deployment diagram with a legend, all four level-1 slots left as placeholders, and an §8 that is the untouched template)

Diagram notation:

- <https://mermaid.js.org/syntax/c4.html> · <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/docs/syntax/c4.md>

Searches that returned nothing, and how they were run. GitHub's code-search endpoint answers
`401 Unauthorized` without a token in this environment, so each repository was downloaded as a
tarball at `HEAD` and grepped in full, which is exhaustive where code search is not:

- `C4 model`, `Deployment_Node`, `Structurizr` over `arc42/docs.arc42.org-site` `_posts`, `_pages`
  and `_data` — zero matches; `\bC4\b` matches only two decision-matrix cells in tip 9-2.
- `coding guideline`, `coding standard`, `coding convention`, `style guide` over the same trees —
  zero matches.
- `backup` over `arc42/docs.arc42.org-site` — one match (tip 11-5); over
  `arc42/faq.arc42.org-site` and the English template files — zero.
- `\bmust\b` over the template's `07_deployment_view.adoc` and `08_concepts.adoc` and over
  `_pages/section-7.md` and `_pages/section-8.md` — zero matches.
- `example` over the 758-entry tree of `arc42/arc42-template` — zero matches.
- The brief's requested GitHub-wide filename search for `08_concepts` / `08-*concepts*` could not be
  run: code search needs authentication. It was replaced by a GitHub *repository* search (which does
  answer unauthenticated) for `arc42`, `arc42 architecture documentation`, `arc42 template` and
  `arc42 crosscutting`, four queries over two pages each, yielding 222 distinct repositories; the
  top candidates by stars were then probed through the git-trees API for `08[-_]…concept|konzept`
  paths. That is how `DokChess/website_de` and
  `bitsmuggler/arc42-c4-software-architecture-documentation-example` entered this note.
  **[unverified as an exhaustive example hunt — a repository-name search does not reach documents in
  repositories whose name and description omit `arc42`, and the `aim42` organisation was checked by
  listing its eight repositories, of which only `htmlSanityCheck` carries an arc42 document.]**
