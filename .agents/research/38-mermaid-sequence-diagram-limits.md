# 38. The limits of a Mermaid sequence diagram

**Question.** Which constructs does a Mermaid `sequenceDiagram` support, which of them are
unreliable on the renderers this catalogue is read through, and what limits must therefore bind a
hand-written sequence diagram here? The diagram rulebook
([`design/diagrams.md`](../../docs/design/diagrams.md)) carries a *Renderer limits* list for `classDiagram`
and `C4Component` and nothing for `sequenceDiagram`, and
[#39](https://github.com/dmastapkovich/aiommbot/issues/39) is about to write a section built
entirely from sequence diagrams, so the limits have to be stated before that section is drafted.

Gathered for [#106](https://github.com/dmastapkovich/aiommbot/issues/106). Mermaid cannot be
rendered in this environment, so no claim here rests on a rendered figure: every claim comes from
the grammar, the renderer, the configuration schema, the published documentation, the changelog,
the JavaScript GitHub itself serves, or — for four questions about token boundaries — from running
mermaid's own lexer over an input. [`references.md`](../references.md) lists
`mermaid-js/mermaid` as a reference source, but `.refs/` holds no clone of it here, so every file
was fetched over the network on **2026-09-11**.

Four checks carry the negatives, and each is named again where it is used.

**The tree was grepped in full, three times.** The repository was downloaded as a tarball at the
`mermaid@12.0.0` tag, at the `mermaid@11.17.2` tag and at `develop` HEAD (`pushed_at`
2026-09-10T18:30:13Z); GitHub's code-search endpoint rejects unauthenticated requests with
`401 Unauthorized` here, and an exhaustive grep over the tree is the stronger check anyway. Every
file this note cites is identical between the `mermaid@12.0.0` tag and `develop`: `diff -r` over
`packages/mermaid/src/diagrams/sequence/` reports no difference, and neither does `diff` over
`docs/syntax/sequenceDiagram.md`, `docs/config/math.md`, `docs/config/theming.md`,
`diagrams/common/common.ts`, `utils.ts`, `config.ts`, `setupGraphViewbox.js`,
`schemas/config.schema.yaml` or `CHANGELOG.md`. A `develop` link below therefore describes the
released 12.0.0 as well.

**11.17.2 was diffed against 12.0.0, because a claim about GitHub has to rest on GitHub's
version.** GitHub serves 11.17.2 (section 1.1). `sequenceDiagram.jison` is **byte-identical** at
`mermaid@11.17.2` and `mermaid@12.0.0` — `md5` `9671c5d3469e2e2886bd82830d5153fb` at both — so no
construct in the 12.0.0 grammar can be missing from the parser GitHub runs. Three renderer files do
differ: `sequenceRenderer.ts` in two places (a drop-shadow argument and a `look === 'neo'` branch
on actor height), `svgDraw.js` in 360 lines and `styles.js` in 9. The documentation page differs
too. Every renderer quotation below is therefore taken from the 11.17.2 copy, and each place where
12.0.0 behaves differently is named there.

**The lexer was executed.** Reading a rule cannot settle which of several rules fires, so the
`%lex` section of `sequenceDiagram.jison` at `mermaid@12.0.0` was run under `jison-lex` 0.3.4 — the
version `packages/mermaid/package.json` pins through `"jison": "^0.4.18"` — over the inputs quoted
below. Every token stream written as `→` comes from that run. The parser was not run.

**"Available since" was measured, not inferred.** The grammar was fetched at **73 distinct release
tags**, from 0.2.15 to `mermaid@12.0.0`, and each construct's first-carrying tag is reported with
the last probed tag that lacks it. Section 1.2 gives the four paths the file has lived at and what
bounds the floor.

Anything a primary source did not confirm is marked **[unverified]**. In particular, nothing below
was seen rendered: the renderer was read and its lexer run, but no diagram was drawn.

## 1 The construct table

The table's *On GitHub* column rests on a measurement that has to come first, so the section opens
with it.

### 1.1 What GitHub renders with

The question "does it render on GitHub" cannot be answered from GitHub's documentation.
[*Creating diagrams*](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)
says only that a fenced block with the `mermaid` language identifier is rendered "in GitHub Issues,
GitHub Discussions, pull requests, wikis, and Markdown files", and then, under a heading *Checking
your version of Mermaid*, hands the question back to the reader:

> To ensure GitHub supports your Mermaid syntax, check the Mermaid version currently in use.
>
> ````text
> ```mermaid
>   info
> ```
> ````

So GitHub publishes no version number. It does, however, ship the renderer, and the renderer can be
read.

**GitHub renders each block in a cross-origin iframe.** A blob page containing a
```` ```mermaid ```` fence carries, in place of the rendered figure, a wrapper whose attributes name
the service — read from `https://github.com/mermaid-js/mermaid/blob/develop/README.md`:

```html
<section class="js-render-needs-enrichment render-needs-enrichment position-relative"
  data-identity="…" data-host="https://viewscreen.githubusercontent.com"
  data-src="https://viewscreen.githubusercontent.com/markdown/mermaid?docs_host=https%3A%2F%2Fdocs.github.com"
  data-type="mermaid" aria-label="mermaid rendered output container">
```

The diagram source travels to that iframe as JSON in a `data-json` attribute on an inner
`<div class="js-render-enrichment-target">`, and a `<pre lang="mermaid" aria-label="Raw mermaid
code">` block — inside a `<div class="render-plaintext-hidden">`, with no `<code>` element — stays
in the page as the fallback. Fetching that `data-src` returns a 24-line document whose whole body
is a render shell and two assets:

```html
<link rel="stylesheet" href="/static/assets/mermaid-7616bad5582574bb905a.css"/>
<script src="/static/assets/mermaidMarkdown-7616bad5582574bb905a.js" type="text/javascript"></script>
```

**The version is a literal in that bundle: `11.17.2`.** The bundle passes it to the renderer and to
the error renderer — `await b.renderer.draw(e,t,"11.17.2",b)` and, in the `catch`,
`Kt.draw(e,t,"11.17.2")`, the call that prints "Syntax error in text / mermaid version …" on a bad
diagram. `mermaid@11.17.2` was published 2026-08-25; `mermaid@12.0.0` was published 2026-09-10, the
day before this note, and `registry.npmjs.org/mermaid` gives `dist-tags.latest = 12.0.0`. So
GitHub is one major version behind the current release, and whether it stays there is
**[unverified]** — the bundle is a deployed asset, not a promise. Its name carries the build's
webpack compilation hash, `7616bad5582574bb905a`, which is shared by every asset of one build — the
stylesheet, the entry bundle and every lazily loaded chunk — and changes on the next deploy. It is
not a per-file content hash: the same string names three files with different contents, and the
bundle reads it back out of webpack's own `a.h=()=>"7616bad5582574bb905a"`.

**GitHub sets the configuration, and on two keys it loosens it.** The bundle's own `initialize`
call is:

```js
ka.initialize({ startOnLoad: !1,
  secure: ["secure", "securityLevel", "startOnLoad", "maxTextSize"],
  securityLevel: "antiscript", flowchart: { diagramPadding: 48 },
  gantt: { useWidth: 1200 }, pie: { useWidth: 1200 },
  sequence: { diagramMarginY: 40 },
  theme: "dark" === Ma ? "dark" : "default" });
```

Four consequences follow from that object, and each of them matters to a hand-written diagram:

- `sequence: { diagramMarginY: 40 }` is the *only* sequence key GitHub sets. Every other
  `SequenceDiagramConfig` default in `config.schema.yaml` applies as published — `width: 150`,
  `wrap: false`, `wrapPadding: 10`, `mirrorActors: true`, `showSequenceNumbers: false`,
  `forceMenus: false` — as does `useMaxWidth: true`, which `SequenceDiagramConfig` inherits rather
  than redeclares (it is a `BaseDiagramConfig` property with that default).
- **The four-key `secure` array narrows mermaid's own six-key default rather than extending it.**
  `secure` is mermaid's list of keys a diagram may not override from its own front matter or
  directive, and `config.schema.yaml` gives it the default
  `['secure', 'securityLevel', 'startOnLoad', 'maxTextSize', 'suppressErrorRendering', 'maxEdges']`
  at both 11.17.2 and 12.0.0. GitHub passes four of those six. So `maxTextSize` staying at its
  schema default of `50000` is mermaid's own doing and holds everywhere, not something GitHub
  pinned; what is GitHub-specific is the opposite — `suppressErrorRendering` and `maxEdges` drop out
  of the protected set, so on GitHub a diagram may override those two from its own front matter and
  elsewhere it may not. Every key that is *not* in the array a host passes stays diagram-settable,
  which is what makes `sequence.wrap` and `sequence.forceMenus` reachable from a diagram's front
  matter below.
- **`theme` is pinned; `look` is not.** GitHub sets `theme` from the page's colour mode and sets no
  `look` key. 12.0.0 gives `SequenceDiagramConfig` the defaults `theme: 'redux-color'` and
  `look: 'neo'` — the docs' *Default theme and look (v12.0.0+)* section: "Sequence diagrams use the
  `redux-color` theme and the `neo` look by default". `config/theming.md` lists the precedence,
  highest first: "1. The diagram's own frontmatter or `%%{init}%%` directive. 2. What you passed to
  `mermaid.initialize()`. 3. The diagram type's default, above. 4. The global default (`theme:
  default`, `look: classic`, `layout: dagre`)." GitHub's explicit `theme` is level 2 and so beats
  `redux-color` at level 3; nothing GitHub sets touches `look`, which falls through to level 3. So
  when GitHub ships 12.x the `neo` look **will** reach sequence diagrams there — drop shadows
  included, since `svgDraw.js` already guards `filter: url(#drop-shadow)` and eight other shape
  branches on `look === 'neo'` at 11.17.2. The one-line gloss "Both are only defaults, so anything
  you set yourself wins" belongs to the sequence page's own front-matter example and is about level
  1, the *author's* config — which, given GitHub's four-key array, also means a diagram's
  front-matter `theme:` beats GitHub's page-mode choice.
- `<br/>` in a label survives — but not because of `securityLevel: "antiscript"`. In
  `diagrams/common/common.ts`, identical at 11.17.2 and 12.0.0, `sanitizeText` has no
  `securityLevel` branch at all: it calls `DOMPurify.sanitize` in both of its arms and branches only
  on `config.dompurifyConfig`. The `securityLevel` branch is in `sanitizeMore`, and it reads
  `if (level === 'antiscript' || level === 'strict' || level === 'sandbox') { text =
  removeScript(text); } else if (level !== 'loose') { … replace(/</g, '&lt;') … replace(/=/g,
  '&equals;') … }`. `strict` is mermaid's schema default and takes the same arm as `antiscript`, so
  the escaping arm is reachable only by a level outside the enum. What GitHub's choice of
  `antiscript` buys is stated by the schema's own `meta:enum`: "HTML tags in text are allowed (only
  script elements are removed), and click functionality is enabled" — the click functionality, not
  the line break.

**GitHub sanitises the finished SVG a second time, with its own allow-list.** After
`mermaid.render` returns, the bundle runs:

```js
h.A.sanitize(r, { RETURN_DOM_FRAGMENT: !0,
  HTML_INTEGRATION_POINTS: { foreignobject: !0 },
  ALLOWED_TAGS: Ba, ADD_ATTR: ["transform-origin", "dominant-baseline"] })
```

`r` holds the SVG `mermaid.render` returned — the bundle destructures `{svg: e, …}` from the render
call and assigns `r = e` on the way in. `Ba` is a 102-entry tag allow-list built in the same file.

The elements the sequence code emits are in it, with one exception and one wrinkle. Listing the
`append('…')` calls across
[`svgDraw.js`](https://github.com/mermaid-js/mermaid/blob/mermaid%4011.17.2/packages/mermaid/src/diagrams/sequence/svgDraw.js)
and
[`sequenceRenderer.ts`](https://github.com/mermaid-js/mermaid/blob/mermaid%4011.17.2/packages/mermaid/src/diagrams/sequence/sequenceRenderer.ts)
at `mermaid@11.17.2` gives exactly `a`, `circle`, `defs`, `div`, `feDropShadow`, `filter`,
`foreignObject`, `g`, `line`, `marker`, `path`, `polygon`, `rect`, `switch`, `symbol`, `text`,
`tspan` and `xhtml:div` — the same eighteen at 12.0.0 — and all eighteen survive the pass:
seventeen appear in `Ba` literally, and `xhtml:div` is an XHTML-namespaced `div`, which DOMPurify
admits because it tests the element's local name. Listing `append()` calls in two files is not,
however, a census of what a sequence diagram emits: the render pipeline always inserts a `<style>`
element before calling the renderer (`document.createElement("style")` … `A.insertBefore(B,k)`
immediately ahead of `draw(e,t,"11.17.2",b)`), and `accTitle:`/`accDescr:` add `<title>` and
`<desc>` afterwards. All three are in `Ba`.

**Two things the sequence code can reach are not in `Ba`.** The first is `use`, emitted by
`svgDrawCommon.drawEmbeddedImage` when a participant carries an `@`-prefixed `icon` property;
`image`, emitted for the unprefixed form, is allowed. The second is MathML: `$$ … $$` is a
documented sequence construct (section 1.2's table, and `config/math.md`), KaTeX renders it as
MathML unless `legacyMathML` is set — "By default, MathML is used for rendering mathematical
expressions" — and not one MathML element is in the list. `math`, `semantics`, `annotation`, `mrow`,
`mi`, `mo`, `mn`, `msqrt`, `mfrac` and `mtable` are all absent from the 102 entries. A math label
therefore cannot survive the pass as MathML. **[unverified: what the reader sees instead — the
stripped text, nothing, or a fallback — was not observed, because nothing was rendered.]**

No `ALLOWED_ATTR` is passed, so DOMPurify's defaults apply, and those were read out of the same
served bundle rather than off a moving branch. The bundled copy names itself: `a.version="3.4.14"`.
Its four default attribute lists are in the bundle with 118, 192, 54 and 5 entries; **no entry in
any of the four begins `on`**, `display` is present in the `svg` and `mathMl` lists, and
`xlink:href` in the `xml` list, which reads in full as
`["xlink:href","xml:id","xlink:title","xml:space","xmlns:xlink"]`. The same four lists in source
form are
[`src/attrs.ts`](https://github.com/cure53/DOMPurify/blob/3.4.14/src/attrs.ts) at tag `3.4.14`,
where they are `freeze`-wrapped exports named `html`, `svg`, `mathMl` and `xml` and carry the same
readings. That combination decides the actor-menu row of the table below, and it is spelled out
there.

### 1.2 Reading the two version columns

Two columns need reading instructions.

*Available since* is the first release tag whose copy of
[`sequenceDiagram.jison`](https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/diagrams/sequence/parser/sequenceDiagram.jison)
carries the construct, with the last probed tag that lacks it in parentheses. **The file has lived
at four paths, and all four were tried**: `src/parser/js-sequence-diagram.jison` at 0.2.15,
`src/diagrams/sequenceDiagram/parser/` from 0.2.16 to 7.0.5, `src/diagrams/sequence/parser/` from
8.1.0 to `v9.1.7`, and `packages/mermaid/src/diagrams/sequence/parser/` from `v9.2.0` on. 0.2.15 is
the oldest tag at which any of the four carries a grammar containing `"participant"`; at 0.2.14 and
below none of them does, checked both by probing each path and by reading the git tree at 0.2.15,
0.2.10 and 0.1.0, where the only sequence-shaped grammar is a different file
(`src/parser/sequence.jison`, whose start symbol is `expressions` over a `sequence TB` header).
There are no core tags between 7.0.5 and 8.1.0, so a boundary reported at 8.1.0 is a real boundary
and not a gap in the ladder. Where the changelog names the pull request that introduced a
construct, the entry is quoted in the caveat, and it agrees with the measurement in every case the
table cites. Where the published documentation states a version marker, the marker is quoted, and
the two are compared.

*On GitHub* says **parses**, and the load-bearing evidence for that is the grammar identity
established above: `sequenceDiagram.jison` is byte-identical at `mermaid@11.17.2` and
`mermaid@12.0.0`, so the grammar this table describes *is* the grammar GitHub serves. The chunk
GitHub loads corroborates the renderer half. It is
`https://viewscreen.githubusercontent.com/static/assets/4985-7616bad5582574bb905a.js`, the lazily
loaded sequence module named by the bundle's own loader (`a.e(4985)`) and addressed through
webpack's `a.u = t => t + "-" + a.h() + ".js"` with `a.h() = "7616bad5582574bb905a"`. Fifty-five
names were searched for in its 119 063 bytes — every `LINETYPE` constant the `signaltype` and block
productions assign, plus `autonumber`, `legacy_title`, `acc_descr_multiline`, `CONFIG_START`,
`createParticipant`, `destroyParticipant` and the renderer functions `parseBoxData`, `drawPopup`,
`popupMenuToggle`, `drawEmbeddedImage`, `drawKatex`, `adjustLoopHeightForWrap`,
`calculateCentralConnectionOffset`, `insertDropShadow`, `wrapLabel` and `forceMenus` — and **all
fifty-five are present**. Only names that survive minification can be searched for this way:
module-scope constants such as `ACTOR_TYPE_WIDTH` are renamed and were dropped from the list rather
than counted as missing. That a compiled-in token implies an accepted production is
**[unverified]** — no diagram was parsed — but the grammar diff makes the inference unnecessary.
Every claim about *appearance* is **[unverified]** and marked where it is made.

| Construct | Available since | On GitHub | Caveat |
|---|---|---|---|
| `participant A` | ≤ 0.2.15, the ladder's floor | parses | Declaration order fixes column order — except for a participant introduced by `create`, whose column lands where the creating message falls ([#4707](https://github.com/mermaid-js/mermaid/issues/4707)). The docs say participants are "rendered in order of appearance in the diagram source text" |
| `actor A` | 8.13.0 (not 8.12.1) | parses | Same statement, `draw='actor'`; draws the stick figure instead of the box |
| `participant A as Label` | 0.5.7 (not 0.5.6) — the measurement agrees with the changelog, which credits PR [#265](https://github.com/mermaid-js/mermaid/pull/265) "Allow sequenceDiagram participant aliasing" under [0.5.7](https://github.com/knsv/mermaid/tree/0.5.7) | parses | The only way to get a line break into a participant label: "Line breaks in Actor names requires aliases". The id before `as` **may not contain a space** — see section 2.2 |
| `participant A@{ "type": … }` | `mermaid@11.11.0` (not `mermaid@11.10.0`); changelog: "feat: Added support for new participant types (`actor`, `boundary`, `control`, `entity`, `database`, `collections`, `queue`)" under 11.11.0 | parses | `@` is excluded from a participant id by the `ID` lexer state; inline `"alias"` loses to an external `as` label |
| `box <colour> <label>` … `end` | `v9.4.0` (not `v9.3.0`) | parses | Holds participant declarations only — see section 3; hex colours are rejected; the first word is eaten as a colour if CSS recognises it |
| `autonumber` | 8.4.8 (not 8.4.6) | parses | The keyword; the numbering itself is older — the changelog lists PR [#722](https://github.com/knsv/mermaid/pull/722) "Sequence numbers" under [8.1.0](https://github.com/knsv/mermaid/tree/8.1.0). The `showSequenceNumbers` config it introduced is not in the 8.1.0 sources (zero matches in `sequenceRenderer.js`, `sequenceDb.js`, `svgDraw.js` and `mermaidAPI.js`); it first appears in the sequence renderer at 8.2.0 |
| `autonumber <start> <step>` | 9.1.0 (not 9.0.1) for the production; decimals in 11.15.0 (not 11.14.0) — changelog "feat(sequence): Add support for decimal start and increment values in the `autonumber` directive", docs *Start and Increment values (v11.15.0+)* | parses | The `NUM` token is `([0-9]+(\.[0-9]{1,2})?\|\.[0-9]{1,2})(?=[ \n]+)` — at most two decimal places, and a space or newline must follow |
| `autonumber off` | 9.1.0 (not 9.0.1) | parses | Undocumented: the construct `autonumber off` appears nowhere in the whole `src/docs` tree. The bare word `off` does appear — 23 lines in 14 files, one of them the sequence page's own configuration table |
| `->` `-->` `->>` `-->>` `-x` `--x` | 0.3.1 (not 0.3.0), where the six become literal tokens with a `signaltype` production; 0.2.15 to 0.3.0 compose them from `LINE`/`DOTLINE` plus `ARROW`/`OPENARROW` instead | parses | The docs table is the only statement of what each draws |
| `-)` `--)` | 8.9.0 (not `v8.8.4`) | parses | `SOLID_POINT` / `DOTTED_POINT`; four minor versions younger than the other six, and absent from every 8.8.x tag |
| `<<->>` `<<-->>` | `v11.0.0` (not `v10.9.0`); docs mark both "(v11.0.0+)" | parses | Bidirectional; the renderer moves the start by 3 units under the comment "Shorten start position of bidirectional arrow to accommodate for second arrowhead" |
| Half-arrows — sixteen tokens, listed under the table | `mermaid@11.13.0` (not `mermaid@11.12.3`) | parses | **The docs' version marker is wrong.** They head the table "Half-Arrows (v11.12.3+)", but every token is absent from the grammar at `mermaid@11.12.3` and present at `mermaid@11.13.0`, whose changelog entry is PR [#6789](https://github.com/mermaid-js/mermaid/pull/6789), "feat: Add half-arrowheads (solid & stick) and central connection support". The published table also mislabels two of the sixteen — see under the table |
| Central connection `A->>()B`, `A()->>B`, `A()->>()B` | `mermaid@11.13.0` (not `mermaid@11.12.3`) | parses | Same wrong marker: docs head the section "Central Connections (v11.12.3+)" |
| `activate` / `deactivate` | 6.0.0 (not 0.5.8) | parses | `deactivate` needs a matching activation; the renderer raises "Trying to inactivate an inactive participant" |
| `+` / `-` shorthand on an arrow | 6.0.0 (not 0.5.8) | parses | The `-` form breaks in front of an id beginning with `x` — see section 2 and issues [#1372](https://github.com/mermaid-js/mermaid/issues/1372), [#1707](https://github.com/mermaid-js/mermaid/issues/1707) |
| `note left of A:` / `note right of A:` | ≤ 0.2.15 | parses | One actor only; the `placement` rule takes a single `actor`, not an `actor_pair` |
| `note over A,B:` | ≤ 0.2.15; the changelog credits PR [#252](https://github.com/mermaid-js/mermaid/pull/252) "Support sequenceDiagram \"over\" notes" under [0.5.6](https://github.com/knsv/mermaid/tree/0.5.6), which is where the production was rewritten into its present shape rather than where it first appeared | parses | Exactly two actors: `actor_pair` is `actor ',' actor \| actor`, so a third is a syntax error; a single actor is duplicated by `[].concat($3, $3).slice(0, 2)` |
| `loop <label>` … `end` | 0.3.0 (not 0.2.16) | parses | Label always wrapped — section 4 |
| `alt` / `else` … `end` | 0.3.1 (not 0.3.0) as a distinct construct — at 0.3.0 `"alt"` and `"else"` both return the `loop` token; multiple `else` at 8.1.0 (not 7.0.5), which the changelog credits to PR [#641](https://github.com/mermaid-js/mermaid/pull/641) "SequenceDiagram: Add support for multiple alt else statements" under [8.1.0](https://github.com/knsv/mermaid/tree/8.1.0) | parses | `else` with no label is legal; `else_sections` is right-recursive, so any number of branches |
| `opt <label>` … `end` | 0.3.1 (not 0.3.0) | parses | Same shape as `loop` |
| `par` / `and` … `end` | 7.0.2 (not 7.0.0) — the measurement agrees with the changelog, which credits PR [#470](https://github.com/mermaid-js/mermaid/pull/470) "add par statement to sequenceDiagram" under [7.0.2](https://github.com/knsv/mermaid/tree/7.0.2) | parses | Nesting documented — section 3 |
| `par_over` / `and` … `end` | `v10.2.0` (not `v10.1.0`) | parses | Undocumented: `par_over` and `par over` appear nowhere in `src/docs`. Only the start line type differs (`PAR_OVER_START`); mermaid's own test parses the underscore spelling |
| `critical` / `option` … `end` | 9.1.2 (not 9.1.1) | parses | `option` is optional — "It is also possible to have no options at all" |
| `break <label>` … `end` | 9.1.2 (not 9.1.1) | parses | Body is a plain `document`, so it nests like `loop` |
| `rect <colour>` … `end` | 8.2.3 (not 8.2.2) | parses | The colour is the whole rest of the line and is **not validated**: `RECT_START` takes `message.message` and passes it to the SVG `fill` attribute unchanged, with none of the `CSS.supports` check `box` applies. The docs offer only `rgb()` and `rgba()`. Hex is unusable for the same `#` reason as `box` |
| `create participant B` / `create actor B` | `v10.3.0` (not `v10.2.0`); docs *Actor Creation and Destruction (v10.3.0+)* | parses | "The sender or the recipient of a message can be destroyed but only the recipient can be created". A created participant cannot be pre-declared, so it cannot be ordered or put in a `box` ([#4707](https://github.com/mermaid-js/mermaid/issues/4707), [#5023](https://github.com/mermaid-js/mermaid/issues/5023)) |
| `destroy A` | `v10.3.0` (not `v10.2.0`) | parses | A destroyed participant must have a destroying message after the declaration, else the render fails with a named error |
| `link A: Label @ URL` | 8.13.3 (not 8.13.2) | parses | **Unreachable at GitHub's configuration, reachable if the diagram changes it.** `drawPopup` sets `display` to `'none'` unless `conf.forceMenus`, and the four sites that attach the opening `onclick` — whose body is the string `var pu = document.getElementById('…'); if (pu != null) { pu.style.display = …; }` — are each guarded by `&& !conf.forceMenus`. GitHub's DOMPurify pass allows no `on*` attribute and does allow `display`, so at GitHub's defaults the group is emitted, permanently hidden and unreachable. But `forceMenus` is in neither `secure` list, so a diagram that writes `config: sequence: forceMenus: true` in its own front matter gets `display: 'block !important'`, no `onclick` to strip, and an `<a>` carrying `xlink:href` — which is in DOMPurify's `xml` default list. **[unverified: what that menu looks like, since nothing was rendered]** |
| `links A: {json}` | 8.13.3 (not 8.13.2) | parses | Same popup, same `forceMenus` escape |
| `properties A: {json}` | 8.13.3 (not 8.13.2) | parses | Undocumented: `properties` and `details` appear nowhere on the sequence page. An `icon` property whose value starts with `@` emits `<use>`, one of the two things GitHub's allow-list omits |
| `details A: {json}` | 8.13.3 (not 8.13.2) | parses | Undocumented, as above |
| `$$ … $$` in a label | `v10.9.0` per the docs heading *Math Configuration (v10.9.0+)* | parses | Not a grammar construct — `$$…$$` is ordinary label text that the renderer intercepts, calling `hasKatex`/`drawKatex` for messages, notes, actor descriptions and loop labels. Documented only in `config/math.md`, whose *Sequence* example is a `sequenceDiagram` with `participant 1 as $$\alpha$$`. **KaTeX's MathML output cannot survive GitHub's allow-list** — see section 1.1 |
| Front matter `config:` block | `v10.4.0` (not `v10.3.0`), measured on `diagram-api/frontmatter.ts`, where `extractFrontMatter` already reads `parsed.config`; `config/configuration.md` marks the feature "Frontmatter (v10.5.0+)", one minor version later | parses | Not a sequence construct: `extractFrontMatter` keeps `title`, `displayMode` and `config`, and `processAndSetConfigs` hands `config` to `addDirective`. `sanitizeDirective` drops keys absent from `configKeys` and `sanitize` deletes the `secure` keys at every depth, so everything else lands. The sequence page demonstrates it with `config: theme: default / look: classic`, and it is the escape hatch behind the `forceMenus` and `wrap` overrides below |
| `%%{init}%%` directive | Same mechanism, and deprecated: "Directives are deprecated from v10.5.0. Please use the `config` key in frontmatter to pass configuration" | parses | Use the front-matter form |
| `%% comment` | 0.3.0 (not 0.2.16) | parses | Must be on its own line; "Any text after the start of the comment to the next newline will be treated as a comment, including any diagram syntax" |
| `# comment` | ≤ 0.2.15 | parses | Undocumented second comment form: `\#[^\n]*` is skipped in the `INITIAL`, `ID`, `ALIAS` and `LINE` states. This is why hex colours and a bare `#` in a label do not work |
| `:wrap:` / `:nowrap:` label prefix | 8.6.0 (not 8.5.2) — at 8.5.2 and below the `<LINE>` rule is the bare `<LINE>[^#\n;]*` and no `wrap` token exists | parses | Undocumented per-label override of `sequence.wrap`; the token is `(?:[:]?(?:no)?wrap:)?` on a block label and `(?:(?:no)?wrap:)?` after the message colon. Exercised in `sequenceDiagram.spec.js` — `2->>3:nowrap: single-line text`, `1->>2:wrap: single-line text` |
| `title <text>` | 9.0.0 (not 8.14.0) — the rule `"title"\s[^#\n;]+` | parses | Undocumented for this diagram type — open issue [#2262](https://github.com/mermaid-js/mermaid/issues/2262) is "Document the title keyword in sequence diagram" |
| `title: <text>` | ≤ 0.2.15 as the two-token statement `title` + a `TXT`/`text2` operand; 9.0.0 as the single `legacy_title` rule `"title:"\s[^#\n;]+` | parses | The colon form is the older of the two, and the only one before 9.0.0 |
| `accTitle:` / `accDescr:` / `accDescr {}` | 9.1.0 (not 9.0.1) — 9.0.0 and 9.0.1 carry a different keyword, `"accDescription"\s[^#\n;]+`, and no `accTitle` at all; the `acc_title`, `acc_descr` and `acc_descr_multiline` states arrive together at 9.1.0 | parses | Accessibility text; not on the sequence page. Adds `<title>` and `<desc>` to the SVG, both in GitHub's allow-list |

### 1.3 The sixteen half-arrow tokens, from the grammar

The lexer defines them in four groups of four. Read left to right: the token, then the line type the
grammar assigns it.

```text
solid, forward        -|\   SOLID_TOP          -|/   SOLID_BOTTOM
                      -\\   STICK_TOP          -//   STICK_BOTTOM
dotted, forward      --|\   SOLID_TOP_DOTTED  --|/   SOLID_BOTTOM_DOTTED
                     --\\   STICK_TOP_DOTTED  --//   STICK_BOTTOM_DOTTED
solid, reverse        /|-   SOLID_ARROW_TOP_REVERSE          \|-   SOLID_ARROW_BOTTOM_REVERSE
                      //-   STICK_ARROW_TOP_REVERSE          \\-   STICK_ARROW_BOTTOM_REVERSE
dotted, reverse      /|--   SOLID_ARROW_TOP_REVERSE_DOTTED  \|--  SOLID_ARROW_BOTTOM_REVERSE_DOTTED
                     //--   STICK_ARROW_TOP_REVERSE_DOTTED   \\--  STICK_ARROW_BOTTOM_REVERSE_DOTTED
```

**Two published rows are unusable as written.** The documentation's half-arrow table prints the
token `\\-` twice — once described as "Solid line with reverse bottom half arrowhead" and once as
"Solid line with reverse bottom stick half arrowhead" — and `\\--` twice the same way. The grammar
gives `\\-` and `\\--` to the *stick* forms only; the solid reverse-bottom tokens are `\|-` and
`\|--`, which the documentation never prints. Anyone copying the first of each duplicated pair gets
a stick arrowhead, not the solid one the row promises.

## 2 Reserved words and characters

The lexer is declared `%options case-insensitive`, so **every keyword below is reserved in any
case** — `End`, `NOTE`, `Alt` and `BOX` are the same tokens as their lower-case spellings. This is
the single most surprising rule in the grammar, and no line of the documentation states it.

### 2.1 Words

Thirty-four keyword literals compete with the generic participant rule, so none of them can open a
line as a bare participant name, and the ones that take an operand cannot be used as that operand
either. **The mechanism is longest match, not rule order.** `jison-lex` scans every rule and takes
the longest match, falling back on file order only to break a tie — which is why `par_over` beats
the earlier `"par"` rule. The consequence is that the thirty-four words are reserved exactly as
whole words: a name that merely begins with one is safe, and running the lexer confirms it —
`endpoint->>db: hi` → `ACTOR("endpoint") SOLID_ARROW("->>") ACTOR("db") TXT(": hi")`, and the same
for `andrew`, `optimizer` and `titleService`. `end` on its own line → `end("end")`. Grouped by what
they open:

| Group | Words |
|---|---|
| Diagram header | `sequenceDiagram` |
| Participants | `participant`, `actor`, `create`, `destroy`, `as`, `box` |
| Blocks | `loop`, `rect`, `opt`, `alt`, `else`, `par`, `par_over`, `and`, `critical`, `option`, `break`, `end` |
| Notes | `note`, `over`, `left of`, `right of` |
| Activation | `activate`, `deactivate` |
| Numbering | `autonumber`, `off` |
| Actor metadata | `links`, `link`, `properties`, `details` |
| Text | `title`, `accTitle`, `accDescr` |

`left of` and `right of` are single tokens containing a space, so a participant may not be named
`left` followed by `of`. `and` is reserved everywhere, not only inside `par` — a participant cannot
be called `and`. Three of the thirty-four bite only in a particular shape: `title` matches as
`"title"\s[^#\n;]+` or `"title:"\s[^#\n;]+`, and `accTitle` and `accDescr` only when followed by a
colon or `{`, so a participant named `title` is safe when an arrow follows it immediately and unsafe
when a space does. The `par_over` keyword takes an underscore, and the longer literal wins over
`par`: mermaid's own test *it should handle par_over statements* parses `par_over Parallel overlap`
and asserts the label.

The documentation states one of these thirty-four, and states it as a hazard rather than a
rule:

> A note on nodes, the word "end" could potentially break the diagram, due to the way that the
> mermaid language is scripted.
>
> If unavoidable, one must use parentheses(), quotation marks "", or brackets {},[], to enclose the
> word "end". i.e : (end), [end], {end}.

Checked against `packages/mermaid/src/docs/syntax/sequenceDiagram.md` at the `mermaid@12.0.0` tag —
the page a reader of this diagram type would consult — `par_over`, `par over`, `autonumber off`,
`properties`, `details`, `icon`, `wrap:` and `nowrap:` all return **zero matches**, and a
word-boundary grep of the same page for `title`, `accTitle` and `accDescr` also returns zero. Seven
of the thirty-four reserved words — `par_over`, `off`, `properties`, `details`, `title`, `accTitle`
and `accDescr` — are therefore reserved by a grammar nobody reading the documentation would know
about.

Four of those eight terms are undocumented across the whole tree and four are not, and the
difference matters. `par_over`, `par over`, `autonumber off` and `nowrap:` return zero over all of
`packages/mermaid/src/docs`; so does `:wrap:`, while the bare `wrap:` matches once (`syntax/c4.md`,
a `wrap: false` config line). `properties` (11 files), `details` (13) and `icon` (28) are all
documented elsewhere for other diagram types — `icon` has a page of its own in `config/icons.md`
and an `@{ icon: … }` shape in `syntax/flowchart.md`, which is precisely the shape a reader would
expect the sequence `@{ }` form to share, and it is never documented for a sequence participant.

### 2.2 Characters

Four lexer rules decide what a participant may be called, and they do not agree with each other.

**A declared id** — the operand of `participant`, `actor`, `activate`, `deactivate` or `destroy` —
is lexed in the `ID` state, which has **three** `ACTOR` rules, one per following context:

```text
<ID>[^\<->\->:\n,;@\s]+(?=\@\{)      before an @{ } config object — no whitespace
<ID>[^<>:\n,;@\s]+(?=\s+as\s)        before an `as` alias        — no whitespace
<ID>[^<>:\n,;@]+(?=\s*[\n;#]|$)      a bare declaration          — whitespace allowed
```

Only the bare form admits a space. None of the three admits `<`, `>`, `:`, `,`, `;`, `@` or a
newline; a `<` in that position matches `<ID>[^<>:\n,;@]*\<[^\n]*` and is returned as the token
`INVALID`, which the grammar silently discards as an empty line, so the participant is never
declared and the first message that mentions it declares it implicitly instead.

**A space in the id silently swallows the `as` alias.** Because the lexer takes the longest match,
the whitespace-tolerant bare rule outruns the `as` rule over the same input. Running the 12.0.0
lexer:

```text
participant order service as Order Service
  →  participant  ACTOR("order service as Order Service")
participant api as API
  →  participant  ACTOR("api")  AS("as")  restOfLine("API")
```

The first line declares one participant whose id is the whole line, with no alias and no `AS`
token. So "spaces are allowed in a declared id" and "always give a participant an `as` label" are
advice that cannot both be taken.

**An id written inline in a message line** is lexed by the generic rule, whose first character class
excludes `/`, `\`, `+`, `(`, `)`, `<`, `-`, `>`, `:`, `,`, `;` and newline. Hyphens are readmitted
by the rule's second half, a negative lookahead against every arrow token. The rule, verbatim from
the grammar, comment and all:

```text
[^\/\\\+\()\+<\->\->:\n,;]+((?!(\-x|\-\-x|\-\)|\-\-\)|\-\|\\|\-\\|\-\/|\-\/\/|\-\|\/|\/\|\-|\\\|\-|\/\/\-|\\\\\-|\/\|\-|\-\-\|\\|\-\-|\(\)))[\-]*[^\+<\->\->:\n,;]+)*             { yytext = yytext.trim(); return 'ACTOR'; } //final_4.11
```

So `order-service->>db: x` parses, but a hyphenated name is not portable into every position, and
that lookahead is the whole safety mechanism.

Six characters need care in any text, and each has a source. Mermaid's own test *should handle
special characters in signals* pins the label half of this down: the input
`Alice->Bob: -:<>,;# comment` is asserted to produce the message `-:<>,`, so a label keeps `-`, `:`,
`<`, `>` and `,`, and is cut at the first `;` or `#`.

| Character | Rule | What to write instead |
|---|---|---|
| `#` | `\#[^\n]*` is skipped as a comment in the `INITIAL`, `ID`, `ALIAS` and `LINE` states | `#35;` — "Numbers given are base 10, so `#` can be encoded as `#35;`" |
| `;` | `";"` returns `NEWLINE`, so a semicolon ends the statement | `#59;` — "Because semicolons can be used instead of line breaks to define the markup, you need to use `#59;` to include a semicolon in message text" |
| `:` | Opens the message text; everything after it up to `#` or `;` or the newline is the label | Nothing — a second `:` inside a label is safe |
| `,` | Separates the two actors of `note over A,B` and is excluded from ids | Use an alias whose label carries the comma |
| `<` `>` | `INVALID` in the `ID` state | Use an alias; `<br/>` in a *label* is fine |
| `%` | `%%` opens a comment; `%%{` opens a directive | Nothing — a single `%` is safe |

The entity mechanism is not sequence-specific, and it runs in two halves.
[`utils.ts`](https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/utils.ts)
defines `encodeEntities`, which rewrites every `#\w+;` to a private placeholder before parsing — a
numeric body to `ﬂ°°NNN¶ß`, a named one to `ﬂ°name¶ß` — and `decodeEntities`, which after rendering
turns those back into HTML entities with
`text.replace(/ﬂ°°/g, '&#').replace(/ﬂ°/g, '&').replace(/¶ß/g, ';')`. That is why the
documentation's example `A->>B: I #9829; you!` works and why HTML character names are accepted too.

**Hex colours cannot be used anywhere in a sequence diagram.** The documentation says so for `box`:

> **Hex colors** (e.g., `#ff0000`) are currently **not supported** as the `#` character is
> interpreted as comment syntax.

and the source agrees in a comment above `parseBoxData` — "The color can be rgb,rgba,hsl,hsla, or
css code names #hex codes are not supported for now because of the way the char # is handled". The
same `#` rule applies to `rect`, and it is the only rule the two constructs share. Their accepted
colour sets are measured separately and they are not the same set: `box` is validated by
`parseBoxData`, so its set is the one the comment names; `rect` is not validated at all — the
renderer's `RECT_START` case takes `message.message` as the `fill` and passes it to
`svgDrawCommon.drawBackgroundRect`, which writes it straight into the SVG `fill` attribute, with no
`CSS.supports` check. The documentation offers only `rgb()` and `rgba()` for `rect` ("The colors are
defined using rgb and rgba syntax"), so anything beyond those two is **[unverified]** for `rect`:
the code imposes no limit, but what a browser makes of the attribute was not observed.

**A `box` label whose first word is a CSS colour name loses that word.** `parseBoxData` splits the
rest of the line with `/^((?:rgba?|hsla?)\s*\(.*\)|\w*)(.*)$/`, tests the first group with
`window.CSS.supports('color', …)`, and only falls back to treating the whole line as the title when
the test fails. The documentation names the escape hatch — "If your group name is a color you can
force the color to be transparent: `box transparent Aqua`" — which is the same trap stated from the
other side.

## 3 Nesting

**The grammar imposes no depth limit on any block.** A block statement is `<keyword> restOfLine
document end` for `loop`, `rect`, `opt` and `break`; `alt` takes `else_sections`, `par` and
`par_over` take `par_sections`, `critical` takes `option_sections`, and all three of those are
defined over `document` with a right-recursive tail. `document` is `/* empty */ | document line`,
and `line` reaches `statement`, which includes every block form. So `alt` within `loop`, `alt`
within `alt` and `par` within `alt` are all grammatical at any depth, and the mandatory `end` makes
them unambiguous: a nested block's `end` closes the inner block, so a following `else` belongs to
the outer `alt`. No depth is documented as unsupported — established by grepping the sequence page
for `nest`, which returns exactly two matches, both permissive.

Those two matches are the only nesting the documentation promises:

> It is also possible to nest parallel blocks.

> This critical block can also be nested, equivalently to the `par` statement as seen above.

Of the thirty-eight fenced diagram examples on the page, exactly **two** nest a block inside a
block: `par` inside `par`, in *Parallel*, and `rect` inside `rect`, in *Background Highlighting*. So
of the eight block keywords — `loop`, `rect`, `opt`, `alt`, `par`, `par_over`, `critical`, `break` —
two have a worked nested example, `critical` is promised to nest in the prose sentence above and
shown only flat, and five have neither.

**`box` is the exception, and it is a hard one.** Its production is `'box' restOfLine box_section
end`, and `box_section` is built only from `box_line`, which is `SPACE participant_statement |
participant_statement | NEWLINE`. A `box` may therefore contain participant declarations and blank
lines and **nothing else** — no message, no note, no block, and no second `box`. Two open issues sit
on that boundary: [#7664](https://github.com/mermaid-js/mermaid/issues/7664), "Add support for
nested sequence diagram groupings/boxes" (open, `Status: Approved`, five comments, last updated
2026-05-25), asks for exactly the `box`-inside-`box` the grammar refuses; and
[#7236](https://github.com/mermaid-js/mermaid/issues/7236), "sequenceDiagram box broken" (open,
`Type: Bug / Error`, `Status: Approved`, last updated 2026-03-27), is a report from someone who put
a message and a `Note over` inside a `box` and got a render error against mermaid 11.12.2 — which
is the grammar behaving as written, reported as a defect because the error does not say so.

Two more open issues bound the same boundary from the participant side:
[#4707](https://github.com/mermaid-js/mermaid/issues/4707), "Not possible to set the order of
participants that are later created in Sequence Diagram" (open, `Status: Approved`, last updated
2026-05-20), and [#5023](https://github.com/mermaid-js/mermaid/issues/5023), "[Sequence diagram]
Create participant in box" (open, `Contributor needed`, last updated 2026-05-04). A participant
introduced by `create` cannot be declared up front, so neither declaration order nor a `box` can
place it.

**What nesting costs in the renderer.** Depth is not free: `adjustLoopHeightForWrap` re-wraps each
block's own label to the block's measured width, and three open bugs live in the nested case —
[#3950](https://github.com/mermaid-js/mermaid/issues/3950) "Activation blocks inside alt branches"
(open, `Type: Bug / Error`), where a participant activated before an `alt` cannot be deactivated
inside each branch; [#1960](https://github.com/mermaid-js/mermaid/issues/1960), where the first
section label of a `par` or `alt` is not centred like the following ones; and
[#1959](https://github.com/mermaid-js/mermaid/issues/1959), where the activation box "extends
upward" when the `activate` keyword is used rather than the `+` shorthand. All three carry
`Status: Triage` and none has a fix.

## 4 Label limits

**There is no documented length limit, and no length limit in the code.** A word-boundary grep of
the sequence documentation page for `length`, `limit`, `maximum` and `truncat` returns zero matches.
Two global limits exist and neither binds a label: `maxTextSize`, default `50000`, caps the *whole
diagram text*, and `maxEdges`, default `500`, is never read by the sequence diagram — grepping the
whole `packages/mermaid/src` tree for `maxEdges` finds it in `config.type.ts`, `config.schema.yaml`,
a comment in the ELK layout renderer, `flowchart/flowDb.ts`, `agentflow/agentflowDb.ts` and one
documentation diagram, and nowhere under `diagrams/sequence/`. So a sequence diagram has no edge
cap; only the 50 000-character text cap applies, and it cannot be raised on GitHub or anywhere else,
because `maxTextSize` is in mermaid's own `secure` default as well as in GitHub's array.

**A line break is an HTML `br` tag or a two-character `\n` — and which `br` spellings count depends
on the version.** The regex is `lineBreakRegex` in
[`diagrams/common/common.ts`](https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/diagrams/common/common.ts),
and it changed in the major release:

- At `mermaid@12.0.0` it is `/<\/?br\s*\/?>/gi`. The comment above it says the leading slash was
  admitted because "without it the tag survived as literal text wherever labels are rendered as
  plain SVG text instead of HTML".
- At the `mermaid@11.17.2` GitHub serves it is `/<br\s*\/?>/gi`, under the comment "Remove and
  ignore br:s". **`</br>` therefore does not break a line on GitHub**; it survives as literal text.

Neither regex is a closed set of spellings: the `i` flag admits `<BR>` and `<Br/>`, `\s*` admits
`<br   />`, and 12.0.0's optional slash on both sides admits `</br/>` too. `getRows` additionally
replaces a literal two-character `\n` with the same placeholder, so both work in both versions. The
documentation demonstrates `<br/>` in messages and notes and states the one place it does not work:

> Line breaks in Actor names requires aliases.

which is the `participant A as Alice<br/>Johnson` form — a break has to go in the label, never in
the id, because the `ID` lexer state would take `<` as `INVALID`.

**Wrapping is off by default for messages and always on for block labels.** That asymmetry is the
most consequential thing in this section, and it comes from three places in the renderer:

- `sequence.wrap` has schema default `false`, and GitHub does not change it. **A diagram may.**
  `wrap` is in neither mermaid's six-key `secure` default nor GitHub's four-key array, and front
  matter outranks `mermaid.initialize()` in the published precedence list, so
  `config: sequence: wrap: true` in a diagram's own front matter turns automatic message wrapping
  on — on GitHub included. Everything below is the behaviour at the default, not a renderer
  constraint.
- For a message, `buildMessageModel` wraps only `if (msg.wrap && msg.message)`, to
  `getMax(boundedWidth + 2 * wrapPadding, conf.width)`. With wrap off, the returned width is
  `getMax(msgDims.width + 2 * wrapPadding, boundedWidth + 2 * wrapPadding, conf.width)` — the
  measured width of the *whole label on one line*. **At the default configuration a long message
  label is never truncated and never wrapped; it pushes the two lifelines apart.**
- For a block label — `loop`, `alt`, `else`, `opt`, `par`, `and`, `critical`, `option`, `break` —
  `adjustLoopHeightForWrap` is called for every block line type, at ten call sites, and its wrapping
  is guarded on the block's measured width rather than on the wrap config:
  `if (msg.id && msg.message && loopWidths[msg.id])` then
  ``msg.message = utils.wrapLabel(`[${msg.message}]`, loopWidth - 2 * conf.wrapPadding, textConf)``
  followed by `msg.wrap = true`. Since the guard never consults `sequence.wrap`, a block label wraps
  to the block's own measured width whatever the configuration says.

Actor descriptions and notes have their own widths, all derived from `sequence.width`, default
`150`: an actor description wraps at `conf.width - 2 * conf.wrapPadding` (130 at the defaults), a
note over one actor at `getMax(conf.width, fromActor.width)`, a box name at
`totalWidth - 2 * conf.wrapPadding`.

**Writing your own `<br/>` switches automatic wrapping off for that label — reliably at 12.0.0, less
so at the version GitHub serves.** `wrapLabel` in
[`utils.ts`](https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/utils.ts)
returns the label untouched when it already contains a break, so a hand-broken block label comes
out exactly as written, which is the only way to control where a block label breaks. The guard is
not the same code in both versions: at 12.0.0 it is `if (common.hasBreaks(label)) { return label; }`
over a non-global `lineBreakTestRegex`, added with the comment "`.test()` on a global regex advances
`lastIndex`, so repeated calls alternate between true and false on the same input"; at
`mermaid@11.17.2` it is `if (common.lineBreakRegex.test(label)) { return label; }` — the global
regex, and the bug that comment describes. On GitHub, therefore, whether a hand-broken label is
returned untouched depends on the `lastIndex` the shared regex happens to be carrying.
**[unverified: how often that bites in practice — `wrapLabel` is memoised and nothing was run
beyond the lexer.]** When `wrapLabel` does wrap, it splits on spaces, and a single word wider than
the limit is broken with `breakString(word, maxWidth, '-', config)` — hyphenated mid-word, not
overflowed.

**What a long label costs on GitHub.** `conf.useMaxWidth` defaults to `true`, and
`calculateSvgSizeAttrs` turns that into `width="100%"` plus `style="max-width: <width>px"`.
GitHub's viewscreen then sets `preserveAspectRatio="xMinYMin"`, supplies the missing `height`
attribute from the `viewBox` (`l.hasAttribute("height") || l.setAttribute("height", c)`), and
computes the iframe height as `this.width / m` times the measured height when the container is
narrower than the `viewBox` width `m`. Those two facts
together mean a diagram wider than the reading column is **scaled down to fit, not scrolled** —
every glyph in it shrinks in proportion. So on GitHub the practical limit on a message label is not
a character count; at the default configuration it is that one long label widens the diagram and
shrinks the type of every other label in it. **[unverified: the visual result was not seen — the
renderer and GitHub's wrapper were read, not run.]** Two open issues are consistent with it:
[#6447](https://github.com/mermaid-js/mermaid/issues/6447) "lifelines are cut off in sequence
diagrams" (open, `Status: Approved`, last updated 2026-04-23), filed against a medium-sized diagram
in a Markdown file, and [#8215](https://github.com/mermaid-js/mermaid/issues/8215), "Sequence
diagram: long labels in the database actors rendering without padding" (open, filed 2026-09-04).

## 5 Known defects that survive today

The set was built from two searches on 2026-09-11 — `is:issue is:open sequenceDiagram in:title`,
which returned 17, and `is:issue is:open label:"Graph: Sequence"`, which returned 55 — and filtered
to the ones that change what a hand-written diagram may say. Enhancement requests are included only
where the request *documents* a limit. Every issue named in this note was then fetched individually
through `api.github.com/repos/mermaid-js/mermaid/issues/<n>`, so the state, title, labels, dates and
comment counts below are read from the issue itself rather than from the search result; all
twenty-six were `open`. Two of them, [#4707](https://github.com/mermaid-js/mermaid/issues/4707) and
[#5023](https://github.com/mermaid-js/mermaid/issues/5023), are discussed in section 3 rather than
in the table, because what they bound is where a `create`d participant's column can go.

Titles are quoted as the tracker spells them, so that a reader can match a row against a search.

| Issue and title | Opened | Last updated | What it means for a diagram here |
|---|---|---|---|
| [#1372](https://github.com/mermaid-js/mermaid/issues/1372) "Deactivating participants starting with \"x\" causes syntax error in sequence diagram" | 2020-04-27 | 2023-08-28 | `John-->>-xAlice: …` is a syntax error, because the lexer takes the longest match and `-x` is two characters where the deactivation `-` is one. Running it: `A-->>-xStore: get` → `ACTOR("A") DOTTED_ARROW("-->>") SOLID_CROSS("-x") ACTOR("Store")`. The reporter's own diagnosis — "I assume the parser mixes this with the `-x` symbol" — is what the grammar says. Workarounds in the issue: a space before the name, or the explicit `deactivate` statement |
| [#1707](https://github.com/mermaid-js/mermaid/issues/1707) "Sequence diagram X in transition/line definition without space causes syntax error" | 2020-10-06 | 2023-12-05 | The same defect with an upper-case id, `D->>-X: test` → `ACTOR("D") SOLID_ARROW("->>") SOLID_CROSS("-X") TXT(": test")`, and the same fix. `Status: Approved`, `Internals: Parser`, `Contributor needed`, `Good first issue!`. The reporter asks for the docs to be changed, which has not happened |
| [#7664](https://github.com/mermaid-js/mermaid/issues/7664) "Add support for nested sequence diagram groupings/boxes" | 2026-04-26 | 2026-05-25 | `Type: Bug / Error`, `Status: Approved`, five comments. Confirms `box` inside `box` is not supported |
| [#7236](https://github.com/mermaid-js/mermaid/issues/7236) "sequenceDiagram box broken" | 2025-12-11 | 2026-03-27 | `Type: Bug / Error`, `Status: Approved`. A `box` containing a message and a `Note over` fails to render; the reporter also notes it renders on `mermaidchart.com` and fails in the Live Editor and in 11.12.2, so behaviour differs between hosts of the same syntax |
| [#3950](https://github.com/mermaid-js/mermaid/issues/3950) "Activation blocks inside alt branches" | 2022-12-27 | 2023-12-13 | `Status: Triage`. A participant activated before an `alt` cannot be deactivated once per branch. Keeps activations and `alt` branches apart |
| [#1959](https://github.com/mermaid-js/mermaid/issues/1959) "SequenceDiagram activation box extends upward on use of \"activate\" keyword" | 2021-03-25 | 2023-07-29 | `Status: Triage`, `Internals: Parser`. The `activate` statement and the `+` shorthand do not draw the same box |
| [#1960](https://github.com/mermaid-js/mermaid/issues/1960) "SequenceDiagram text for the first section of `par` & `alt` is not centered the same way as following section" | 2021-03-25 | 2023-07-29 | `Status: Triage`, zero comments. Cosmetic but unfixed for five years: the first branch label of a multi-branch block sits differently from the rest |
| [#2136](https://github.com/mermaid-js/mermaid/issues/2136) "Empty message in sequence diagram not tolerated on last statement" | 2021-06-16 | 2025-05-28 | `A --> B: ` with nothing after the colon renders everywhere except as the last line of the diagram. Give every arrow a label |
| [#6054](https://github.com/mermaid-js/mermaid/issues/6054) "when code end with space, mermaid.parse return true but mermaid.run throw error" | 2024-11-13 | 2026-03-02 | `Status: Approved`. Trailing whitespace at the end of the diagram can pass validation and fail rendering |
| [#4293](https://github.com/mermaid-js/mermaid/issues/4293) "Update to Mermaid 10.1.0 breaks sequenceDiagram with blank after \"autonumber\" definition" | 2023-04-12 | 2023-06-12 | A trailing space on the `autonumber` line produced `Parse error on line 2 … Expecting 'NEWLINE', 'NUM', 'off', got 'participant_actor'` in 10.1.0 after working in 10.0.2. **[unverified whether it still reproduces]** — the lexer still skips `\s+` including newlines in the rule after the `[\n]+` newline rule, which is the plausible mechanism, but this input was not run |
| [#5419](https://github.com/mermaid-js/mermaid/issues/5419) "Hash \"#\" symbol as prefix is not working for sequenceDiagram" | 2024-03-27 | 2024-03-27 | `actor Alice as #1` and `Note over Bob: #55` come out empty. The `#` comment rule explains it; the entity form `#35;1` is the documented way |
| [#1399](https://github.com/mermaid-js/mermaid/issues/1399) "sequenceDiagram Title disappears when Dark theme applied" | 2020-05-10 | 2026-03-13 | GitHub sets `theme: "dark"` from the page's `data-color-mode`, so a `title` line is at risk for readers in dark mode. Six years open |
| [#1279](https://github.com/mermaid-js/mermaid/issues/1279) "sequenceDiagram Links" | 2020-02-26 | 2026-03-17 | `Status: Approved` enhancement, 24 comments, still open; together with [#7237](https://github.com/mermaid-js/mermaid/issues/7237) "Syntax Proposal: Add clickable HTTP links to sequence diagram elements (participants, actors, messages, notes)" (`Status: Approved`, opened 2025-12-11) it establishes that a sequence diagram has no clickable link other than the actor popup menu |
| [#2262](https://github.com/mermaid-js/mermaid/issues/2262) "Document the title keyword in sequence diagram" | 2021-08-23 | 2023-08-09 | `Area: Documentation`, open for five years; the `title` keyword remains undocumented for this diagram type |
| [#2199](https://github.com/mermaid-js/mermaid/issues/2199) "Support note text that spans multiple lines in sequence diagram" | 2021-07-18 | 2026-04-17 | Open. A multi-line note needs explicit `<br/>`, not source line breaks |
| [#4381](https://github.com/mermaid-js/mermaid/issues/4381) "Add Markdown Strings to sequence diagrams" | 2023-05-08 | 2025-07-17 | Carries both `Status: Approved` and `Status: In progress`, the latter since 2023. Grepping the whole `src/docs/syntax/` directory for markdown strings finds them documented for `flowchart`, `mindmap` and `usecase`, and referenced by `swimlanes` (which defers to the flowchart page), never for `sequenceDiagram`; [#5460](https://github.com/mermaid-js/mermaid/issues/5460) "adding Markdown to SequenceDiagram Notes" (opened 2024-04-13) asks the same for notes. So no bold, italic or list inside a sequence label |
| [#523](https://github.com/mermaid-js/mermaid/issues/523) "Styling components of the sequence diagram" | 2017-04-20 | 2026-07-01 | `Status: Approved` for nine years, 103 comments, with [#2314](https://github.com/mermaid-js/mermaid/issues/2314) "Ability to style the sequenceDiagram participants" (2021-09-16) and [#6367](https://github.com/mermaid-js/mermaid/issues/6367) "customize the color of participant in the  sequenceDiagram" (2025-03-11, last updated 2026-03-02) asking for per-participant colour. There is no per-participant or per-message styling in the syntax; colour is available only through `box`, `rect` and the theme |
| [#6993](https://github.com/mermaid-js/mermaid/issues/6993) "Sequence Diagram \"Note over A\" KaTeX extra padding" | 2025-09-24 | 2026-08-06 | `Status: Approved`, `Good first issue!`. The only open issue on the `$$ … $$` math construct, and it is about layout, not about the sanitiser question section 1.1 raises |

**Four defects are in the documentation rather than the code**, and all four were found by comparing
the published page with a machine-readable source rather than by reading an issue. Two came out of
the grammar comparison: the half-arrow and central-connection sections are labelled `(v11.12.3+)`
when the tokens first appear at `mermaid@11.13.0`, and the half-arrow table prints `\\-` and `\\--`
in two rows each, assigning the stick tokens to the solid descriptions. Two more came out of
comparing the page's *Possible configuration parameters* table with `config.schema.yaml`:
`mirrorActors` is published with default `false` where `SequenceDiagramConfig` and GitHub's served
bundle both give `true`, and the `actorFontWeight`, `noteFontWeight` and `messageFontWeight` rows
print a font-family string in the Default column ("Open Sans", sans-serif and "trebuchet ms",
verdana, arial) where the schema says `400`. None of the four has an issue number; no search was run
for one, so whether they are known is **[unverified]**.

## 6 The limits, as they would be written down

Eleven rules. Each is stated positively, with the reason that makes it a rule rather than a
preference. They are stated here, not applied: editing the rulebook is #39's job, and the rulebook
already carries its own *Renderer limits* list for the other diagram kinds.

1. **Write every participant with an explicit `participant` or `actor` line, in reading order, and
   give it a short `as` label whose id contains no space.** Declaration order is the only control
   over column order; the `as` label is the only way to get a line break, a comma or a reserved word
   into a participant's visible name; and the declared-id lexer state accepts characters the inline
   one refuses. The space matters because the longest-match lexer folds the alias into the id
   otherwise: `participant order service as Order Service` declares one participant named
   `order service as Order Service`. The one participant this rule cannot cover is one introduced by
   `create`, which cannot be declared up front at all — its column lands where the creating message
   falls, and neither declaration order nor a `box` moves it
   ([#4707](https://github.com/mermaid-js/mermaid/issues/4707),
   [#5023](https://github.com/mermaid-js/mermaid/issues/5023)).
2. **Keep every participant id clear of the 34 reserved words, and never write the `-` deactivation
   shorthand in front of an id.** The reserved words bite in *any* case — `End`, `NOTE`, `Alt` and
   `BOX` are the same tokens as their lower-case spellings — so casing is not a control over them
   and a lower-case convention buys nothing here; what protects an id is that the lexer takes the
   longest match, so a word that merely *begins* with a keyword (`endpoint`, `optimizer`) is safe.
   The shorthand is the real hazard, and only in one position: `A->>xStore: get` parses, while
   `A-->>-xStore: get` lexes `-x` as the cross arrow and fails. Prefer explicit `activate` and
   `deactivate` statements, which is the workaround both
   [#1372](https://github.com/mermaid-js/mermaid/issues/1372) and
   [#1707](https://github.com/mermaid-js/mermaid/issues/1707) name and which these issues have kept
   open since 2020. Lower-case-with-underscores remains a reasonable house convention for
   legibility; it is a convention, not a consequence of the grammar.
3. **Keep `#` and `;` out of every label.** `#` opens a comment in four lexer states and `;` ends
   the statement; the documented escapes are `#35;` and `#59;`. The same rule forbids hex colours
   anywhere in the diagram. Write a `box` colour as `rgb()`, `rgba()`, `hsl()`, `hsla()` or a CSS
   colour name, which is the set `parseBoxData`'s own comment names and `CSS.supports` enforces; for
   `rect` the documentation offers only `rgb()` and `rgba()`, and since the renderer validates
   nothing there, stay inside the documented two.
4. **Start a `box` label with a word that is not a CSS colour, or write `box transparent <label>`.**
   `parseBoxData` tests the first word with `CSS.supports('color', …)` and eats it when the test
   passes, so `box Purple team` is a purple box labelled "team".
5. **Put nothing but `participant` and `actor` lines inside a `box`, and never nest one.**
   `box_section` is built from `participant_statement` alone, which is why
   [#7236](https://github.com/mermaid-js/mermaid/issues/7236) reads as a defect and
   [#7664](https://github.com/mermaid-js/mermaid/issues/7664) is still a request.
6. **Nest `alt`, `opt`, `loop`, `par`, `critical`, `break` and `rect` freely, but stop at two
   levels.** The grammar imposes no depth limit and the mandatory `end` keeps deep nesting
   unambiguous, so the limit is a reading limit, not a parser limit — and the three open renderer
   bugs in the nested case ([#3950](https://github.com/mermaid-js/mermaid/issues/3950),
   [#1959](https://github.com/mermaid-js/mermaid/issues/1959),
   [#1960](https://github.com/mermaid-js/mermaid/issues/1960)) all concern labels and activation
   boxes inside branches.
7. **Give every arrow a label, and keep the label short enough to read at column width.** An empty
   label breaks the diagram when it is the last statement
   ([#2136](https://github.com/mermaid-js/mermaid/issues/2136)). A long one is neither wrapped nor
   truncated *at the default configuration*: `sequence.wrap` is `false`, so the lifelines move
   apart, the `viewBox` grows, and GitHub scales the whole figure down to the reading column,
   shrinking every other label with it. This is a choice, not a renderer limit — `wrap` is in
   neither `secure` list, so a diagram may set `config: sequence: wrap: true` in its own front
   matter and wrap on GitHub. The catalogue declines it, because automatic wrapping measures against
   `sequence.width` (default `150`) and puts the break wherever the measurement falls, which makes
   the rendered shape of a figure depend on font metrics rather than on what the author wrote. Short
   labels and rule 8 give the same readability with the break under the author's control.
8. **Break a long note or block label yourself with `<br/>`.** `wrapLabel` returns any label that
   already contains a break untouched, so a hand-broken label is the one whose line breaks the
   author chooses; automatic wrapping otherwise measures against `sequence.width`, default `150`.
   Two caveats, both from section 4: write `<br/>` and not `</br>`, because the 11.17.2 regex GitHub
   serves does not match the malformed spelling; and the 11.17.2 guard tests a global regex, so the
   untouched-return is not guaranteed on GitHub. Keeping labels short enough that wrapping never
   triggers is the robust form of this rule.
9. **Use no construct newer than mermaid `11.15.0`, which is the measured ceiling; a stricter floor
   is a judgement call this note does not make for you.** `11.15.0` is the newest *Available since*
   value in the table, so that ceiling admits every construct listed, including the `@{ }`
   participant config (`mermaid@11.11.0`), the half-arrows and `()` central connections
   (`mermaid@11.13.0`) and decimal `autonumber` values (`mermaid@11.15.0`). The measurement supports
   nothing stricter: GitHub serves `11.17.2` and the grammar it runs is byte-identical to 12.0.0's,
   so every construct in the table parses there today. Two things the measurement does **not**
   settle. First, only one renderer was measured. The question above says "renderers", plural, and
   this note read exactly one — the Live Editor and `mermaidchart.com` are named in the
   [#7236](https://github.com/mermaid-js/mermaid/issues/7236) row precisely because behaviour
   differed between them, and neither was read here. A floor below the ceiling has to come from the
   oldest renderer a diagram is read through, and that renderer has not been identified. Second,
   GitHub publishes no version — its documentation tells the reader to render an `info` diagram to
   find out — so the version behind a catalogue diagram is an observation with a shelf life. That
   shelf life argues for the ceiling, not against it: nothing observed here shows GitHub's version
   moving backwards, and a renderer that only moves forward makes a newer construct more likely to
   parse over time, not less. If #39 wants a margin below `11.15.0`, it should state the margin as a
   deliberate choice and give its reason.
10. **Prefer prose or the inventory table next to the figure to a `link` in the diagram.** At
    GitHub's configuration the popup is unreachable: `drawPopup` draws it as `<g display="none">`
    and the only thing that opens it is an inline `onclick`, which GitHub's DOMPurify pass strips
    while allowing `display`. But this is a configuration, not an impossibility — `forceMenus` is
    in neither `secure` list, so a diagram that sets `config: sequence: forceMenus: true` in its own
    front matter gets a permanently visible menu whose `<a>` carries `xlink:href`, an attribute
    DOMPurify allows by default, and no `onclick` for the sanitiser to remove. The catalogue still
    keeps links out of the figure, for the reason the rulebook already reached for C4 boxes: a menu
    that is always open is not a link affordance a reader recognises, and the diagram source is not
    where a reader looks for a URL. **[unverified: what the forced menu looks like, since nothing
    was rendered.]**
11. **Use no construct the documentation does not describe on the page for this diagram type.**
    `par_over`, `autonumber off`, `properties`, `details`, participant icons, `title`, `accTitle`,
    `accDescr` and the `:wrap:`/`:nowrap:` prefixes are all in the grammar and none is on the
    sequence page; a reader cannot look them up, and an undocumented construct is the first thing a
    rewrite of the parser drops. One construct is documented but only elsewhere: `$$ … $$` math has
    its own page, `config/math.md`, with a worked `sequenceDiagram` example, and the sequence page
    never mentions it — so treat it as off-page, unlike the front-matter `config:` block, which the
    sequence page does demonstrate. Two of these cases carry a concrete cost at GitHub's sanitiser
    and not merely a discoverability one: the `@`-prefixed `properties` `icon` emits `<use>`, and
    KaTeX math emits MathML, and neither is in GitHub's 102-tag allow-list.

## Sources

Mermaid, in source form. The repository was downloaded as a tarball three times — at the
`mermaid@12.0.0` tag, at the `mermaid@11.17.2` tag and at `develop` HEAD (`pushed_at`
2026-09-10T18:30:13Z) — and grepped in full. `diff -r` over `packages/mermaid/src/diagrams/sequence/`
and `diff` over each of `docs/syntax/sequenceDiagram.md`, `docs/config/math.md`,
`docs/config/theming.md`, `diagrams/common/common.ts`, `utils.ts`, `config.ts`,
`setupGraphViewbox.js`, `schemas/config.schema.yaml` and `CHANGELOG.md` report no difference between
`mermaid@12.0.0` and `develop`, so the `develop` links below describe the released 12.0.0 as well:

- <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/diagrams/sequence/parser/sequenceDiagram.jison> — the grammar; the authority on reserved words, arrow tokens, nesting and the `box` body
- <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/diagrams/sequence/sequenceDb.ts> · <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/diagrams/sequence/sequenceRenderer.ts> · <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/diagrams/sequence/svgDraw.js>
- <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/diagrams/sequence/sequenceDiagram.spec.js> — the `par_over`, `wrap:`/`nowrap:` and special-character tests quoted above
- <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/diagrams/common/common.ts> — `lineBreakRegex`, `getRows`, `hasBreaks`, `sanitizeText`, `sanitizeMore`
- <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/diagrams/common/svgDrawCommon.ts> — `drawEmbeddedImage` (the `use` element) and `drawBackgroundRect` (the `rect` fill)
- <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/utils.ts> — `wrapLabel`, `breakString`, `encodeEntities`, `decodeEntities`
- <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/config.ts> — `sanitize`, `addDirective`, `getEffectiveHtmlLabels`
- <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/utils/sanitizeDirective.ts> · <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/defaultConfig.ts> — `configKeys`, the flat set of every key name a directive may carry
- <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/diagram-api/frontmatter.ts> · <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/preprocess.ts> · <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/mermaidAPI.ts> — `extractFrontMatter` and `processAndSetConfigs`, the path a diagram's own `config:` block takes
- <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/setupGraphViewbox.js> — `calculateSvgSizeAttrs`, the `useMaxWidth` behaviour
- <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/schemas/config.schema.yaml> — `SequenceDiagramConfig`, `BaseDiagramConfig`, the `secure` default and the global `maxTextSize` / `maxEdges` defaults
- <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/CHANGELOG.md> — 2203 lines, back to 0.1.0; the source of every quoted release entry
- <https://github.com/mermaid-js/mermaid/tree/mermaid%4011.17.2/packages/mermaid/src/diagrams/sequence> — the version GitHub serves, from which every renderer quotation above is taken. `parser/sequenceDiagram.jison` is byte-identical to the 12.0.0 copy (`md5` `9671c5d3469e2e2886bd82830d5153fb`); [`svgDraw.js`](https://github.com/mermaid-js/mermaid/blob/mermaid%4011.17.2/packages/mermaid/src/diagrams/sequence/svgDraw.js), [`sequenceRenderer.ts`](https://github.com/mermaid-js/mermaid/blob/mermaid%4011.17.2/packages/mermaid/src/diagrams/sequence/sequenceRenderer.ts) and `styles.js` are not
- <https://github.com/mermaid-js/mermaid/blob/mermaid%4011.17.2/packages/mermaid/src/diagrams/common/common.ts> — the 11.17.2 `lineBreakRegex`, quoted against the 12.0.0 one in section 4
- <https://github.com/mermaid-js/mermaid/blob/8.2.0/src/diagrams/sequence/sequenceRenderer.js> — where `showSequenceNumbers` first appears; absent from the 8.1.0 sources the changelog credits with sequence numbering
- The grammar at the boundary tags each *Available since* cell names, one link per path: <https://github.com/mermaid-js/mermaid/blob/0.2.15/src/parser/js-sequence-diagram.jison> · <https://github.com/mermaid-js/mermaid/blob/0.5.7/src/diagrams/sequenceDiagram/parser/sequenceDiagram.jison> · <https://github.com/mermaid-js/mermaid/blob/7.0.2/src/diagrams/sequenceDiagram/parser/sequenceDiagram.jison> · <https://github.com/mermaid-js/mermaid/blob/8.1.0/src/diagrams/sequence/parser/sequenceDiagram.jison> · <https://github.com/mermaid-js/mermaid/blob/8.6.0/src/diagrams/sequence/parser/sequenceDiagram.jison> · <https://github.com/mermaid-js/mermaid/blob/8.9.0/src/diagrams/sequence/parser/sequenceDiagram.jison> · <https://github.com/mermaid-js/mermaid/blob/9.0.0/src/diagrams/sequence/parser/sequenceDiagram.jison> · <https://github.com/mermaid-js/mermaid/blob/9.1.0/src/diagrams/sequence/parser/sequenceDiagram.jison> · <https://github.com/mermaid-js/mermaid/blob/mermaid%4011.13.0/packages/mermaid/src/diagrams/sequence/parser/sequenceDiagram.jison>

Published documentation:

- <https://mermaid.js.org/syntax/sequenceDiagram.html> — fetched 2026-09-11; every version marker on the page was read from it and matches its source file
- <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/docs/syntax/sequenceDiagram.md> — the source of that page, 927 lines, 38 fenced diagram examples
- <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/docs/config/math.md> — *Math Configuration (v10.9.0+)*, whose *Sequence* example is the only documentation of `$$ … $$` in a sequence diagram, and whose *Legacy Support* section states that MathML is the default output
- <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/docs/config/theming.md> — *Per-diagram defaults*, the four-level precedence list quoted in section 1.1
- <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/docs/config/configuration.md> · <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/docs/config/directives.md> — front matter, marked "(v10.5.0+)", and the directive form it deprecates "from v10.5.0"
- <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/docs/syntax/flowchart.md> · <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/docs/syntax/mindmap.md> · <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/docs/syntax/usecase.md> — the three pages that document markdown strings; <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/docs/syntax/swimlanes.md> refers the reader to the flowchart page for them
- <https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/src/docs/config/icons.md> — where `icon` *is* documented, for other diagram types, together with the `@{ icon: … }` shape on the flowchart page

Releases, for the dates:

- <https://github.com/mermaid-js/mermaid/releases/tag/mermaid%4012.0.0> (published 2026-09-10T07:33:03Z) · <https://github.com/mermaid-js/mermaid/releases/tag/mermaid%4011.17.2> (2026-08-25T11:37:31Z), read through `api.github.com/repos/mermaid-js/mermaid/releases/tags/…`; `registry.npmjs.org/mermaid` gives `dist-tags.latest = 12.0.0`
- The tag set came from <https://api.github.com/repos/mermaid-js/mermaid/tags> paginated in full — 235 refs, of which 168 are mermaid core versions. Unprefixed tags run from 0.1.0 to 9.1.6, `v`-prefixed tags from `v9.1.7` through `v11.0.0`, and `mermaid@`-prefixed tags cover the rest of the 11.x line and 12.0.0. There are no core tags between 7.0.5 and 8.1.0, which is why several boundaries land on 8.1.0

GitHub, read as served on 2026-09-11:

- <https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams> · <https://github.com/github/docs/blob/main/content/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams.md> — the page that declines to publish a version
- `https://viewscreen.githubusercontent.com/markdown/mermaid?docs_host=https%3A%2F%2Fdocs.github.com` — the 24-line render shell, named by the `data-src` of the `<section class="js-render-needs-enrichment">` wrapper on <https://github.com/mermaid-js/mermaid/blob/develop/README.md>, whose served HTML also carries the `data-json` attribute and the `<pre lang="mermaid">` fallback quoted in section 1.1
- `https://viewscreen.githubusercontent.com/static/assets/mermaidMarkdown-7616bad5582574bb905a.js` — 1 766 759 bytes; carries the literal `"11.17.2"`, the `initialize` call, the 102-entry `ALLOWED_TAGS` list, the `h.A.sanitize(r, …)` options, the bundled DOMPurify's `a.version="3.4.14"` and its four default attribute lists
- `https://viewscreen.githubusercontent.com/static/assets/4985-7616bad5582574bb905a.js` — 119 063 bytes; the lazily loaded sequence module, in which all 55 searched grammar and renderer names are present
- Both asset URLs carry the build's compilation hash rather than a per-file content hash, so neither is a stable identifier; they were re-fetched on 2026-09-11 at the byte sizes above and change on GitHub's next deploy

DOMPurify, for what GitHub's second sanitising pass keeps. The bundled copy names itself `3.4.14`,
so the source is read at that tag rather than on a moving branch:

- <https://github.com/cure53/DOMPurify/blob/3.4.14/src/attrs.ts> — four frozen default lists (`html`, `svg`, `mathMl`, `xml`); zero entries begin `on`, `display` is in the `svg` and `mathMl` lists, `xlink:href` in the `xml` list. The same four lists were extracted from GitHub's bundle at 118, 192, 54 and 5 entries with the same readings

The lexer, run rather than read:

- `jison-lex` 0.3.4, the version [`packages/mermaid/package.json`](https://github.com/mermaid-js/mermaid/blob/develop/packages/mermaid/package.json) pins through `"jison": "^0.4.18"`, over the `%lex` section of the 12.0.0 grammar. It settled four questions reading could not: that the lexer takes the longest match and not the first (`endpoint`, `andrew`, `optimizer`, `titleService` all lex as `ACTOR`), that `participant order service as Order Service` folds the alias into the id, that `A->>xStore: get` parses while `A-->>-xStore: get` does not, and that `title My title` and `title: My title` reach different tokens

Open issues. Each of the twenty-six was fetched individually from
`api.github.com/repos/mermaid-js/mermaid/issues/<n>` on 2026-09-11, and every title, label, opened
date, last-updated date and comment count quoted above comes from that payload:

- Parser: <https://github.com/mermaid-js/mermaid/issues/1372> · <https://github.com/mermaid-js/mermaid/issues/1707> · <https://github.com/mermaid-js/mermaid/issues/2136> · <https://github.com/mermaid-js/mermaid/issues/4293> · <https://github.com/mermaid-js/mermaid/issues/5419> · <https://github.com/mermaid-js/mermaid/issues/6054>
- `box`, nesting and participant order: <https://github.com/mermaid-js/mermaid/issues/7236> · <https://github.com/mermaid-js/mermaid/issues/7664> · <https://github.com/mermaid-js/mermaid/issues/3950> · <https://github.com/mermaid-js/mermaid/issues/4707> · <https://github.com/mermaid-js/mermaid/issues/5023>
- Renderer: <https://github.com/mermaid-js/mermaid/issues/1399> · <https://github.com/mermaid-js/mermaid/issues/1959> · <https://github.com/mermaid-js/mermaid/issues/1960> · <https://github.com/mermaid-js/mermaid/issues/6447> · <https://github.com/mermaid-js/mermaid/issues/6993> · <https://github.com/mermaid-js/mermaid/issues/8215>
- Missing capabilities, cited as evidence of a limit: <https://github.com/mermaid-js/mermaid/issues/523> · <https://github.com/mermaid-js/mermaid/issues/1279> · <https://github.com/mermaid-js/mermaid/issues/2199> · <https://github.com/mermaid-js/mermaid/issues/2262> · <https://github.com/mermaid-js/mermaid/issues/2314> · <https://github.com/mermaid-js/mermaid/issues/4381> · <https://github.com/mermaid-js/mermaid/issues/5460> · <https://github.com/mermaid-js/mermaid/issues/6367> · <https://github.com/mermaid-js/mermaid/issues/7237>
- Changelog entries quoted for a version: <https://github.com/mermaid-js/mermaid/pull/6789> (half-arrows and central connections, 11.13.0) · <https://github.com/mermaid-js/mermaid/pull/6704> (participant types, 11.11.0) · <https://github.com/mermaid-js/mermaid/pull/7174> (decimal `autonumber`, 11.15.0) · <https://github.com/mermaid-js/mermaid/pull/722> and <https://github.com/mermaid-js/mermaid/pull/641> (8.1.0) · <https://github.com/mermaid-js/mermaid/pull/470> (7.0.2) · <https://github.com/mermaid-js/mermaid/pull/265> (0.5.7) · <https://github.com/mermaid-js/mermaid/pull/252> (0.5.6)

Checks that returned nothing, and how they were run. GitHub's code-search endpoint answers
`401 Unauthorized` without a token here, so every negative rests on a full-tree grep of the
downloaded tarball or on an enumerated set. The scope of each grep is given, because two of these
return zero over one file and not over the tree:

- `par_over`, `par over`, `autonumber off`, `nowrap:` and `:wrap:` over the whole
  `packages/mermaid/src/docs` tree at `mermaid@12.0.0` — zero matches each. The bare `wrap:` is
  **not** zero over the tree: one match, `syntax/c4.md` line 169.
- `properties`, `details` and `icon` over
  `packages/mermaid/src/docs/syntax/sequenceDiagram.md` — zero matches each. Over the whole docs
  tree they match 11, 13 and 28 files, all for other diagram types.
- `title`, `accTitle`, `accDescr` as whole words over the same sequence page — zero matches.
- `length`, `limit`, `maximum`, `truncat` over the same file — zero matches; there is no documented
  label-length rule.
- `nest` over the same file — exactly two matches, both permissive, quoted in section 3.
- `off` as a whole word over the docs tree — 23 matches in 14 files, including the sequence page's
  own `mirrorActors` row, which is why the *undocumented* claim in the table is made for the
  two-word `autonumber off` and not for `off`.
- Block depth over all 38 fenced diagram examples on the sequence page — exactly two nest, `par`
  inside `par` and `rect` inside `rect`.
- `maxEdges` over `packages/mermaid/src` — six sites, none of them under `diagrams/sequence/`.
- Attribute names beginning `on` over all four default lists, both as extracted from GitHub's
  bundle and in DOMPurify's `src/attrs.ts` at tag `3.4.14` — zero matches in either.
- MathML element names over GitHub's 102-entry `ALLOWED_TAGS` — zero matches, checked for `math`,
  `semantics`, `annotation`, `mrow`, `mi`, `mo`, `mn`, `msqrt`, `mfrac` and `mtable`.
- The `append('…')` calls in the sequence renderer and `svgDraw` at `mermaid@11.17.2` — eighteen
  distinct tags, the same eighteen at 12.0.0. Seventeen are in GitHub's 102-entry allow-list
  literally; the eighteenth, `xhtml:div`, is not, and passes only because DOMPurify matches the
  element's local name, which for a d3 `append('xhtml:div')` is `div`. That enumeration covers two
  files and not the whole pipeline: the `<style>` element the render path always inserts, and the
  `<title>`/`<desc>` that `accTitle:`/`accDescr:` add, are not `append()` calls in those files, and
  all three are allowed.
- Whether Mermaid's own trackers know about the four documentation defects in section 5 was **not**
  checked: no issue search was run for them, so that they are unreported is **[unverified]**.
- Whether GitHub's rendered output looks as the renderer implies was **not** checked at all: Mermaid
  cannot be rendered in this environment, and every appearance claim in this note is therefore
  marked **[unverified]** where it is made. The lexer was run; the parser and the renderer were not.

