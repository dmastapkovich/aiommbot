# <Component name>

_Status: not started (#N)._
_Layer: Core | Adapter | Generic plugin | Adapter-specific plugin | Testing toolkit._
_ADRs: [ADR-NNNN](../../adr/NNNN-slug.md). Research: [`docs/research/NN`](../../research/NN-slug.md)._

## 1. Purpose and boundaries

One paragraph: what this component is for, where it sits in the building-block view, what is
explicitly outside it.

## 2. Responsibilities and non-responsibilities

- Owns: …
- Does **not** own (and who does): …

## 3. Public contract

The Protocols, types, functions and errors other components or users may depend on. Signatures in
prose or a `classDiagram`; wire formats and invariants stated. Everything not listed here is
`_internal`.

## 4. Internal structure

C4 **Component** (or **Code**) diagram of the pieces inside and their dependencies, followed by a
table: piece → responsibility → why it is separate.

## 5. Interactions

`sequenceDiagram`s for the main scenario and each failure scenario this component is designed
around. Name the collaborating components with their `CONTEXT.md` terms.

## 6. Design patterns

For each pattern applied: the [refactoring.guru](https://refactoring.guru/design-patterns/catalog)
name, the problem it solves *here*, and the alternative that was rejected. Patterns considered and
not used are listed with one line each.

## 7. SOLID analysis

One short paragraph per principle — S, O, L, I, D — arguing how this component satisfies it or
stating honestly where and why it is bent.

## 8. Failure modes and invariants

Invariants that must always hold. What happens on timeout, cancellation, dependency outage, bad
input and concurrent use — each named as a typed outcome or an exception, with the boundary that
converts it — and what is surfaced to observability.

## 9. Rules that bind this component

The `ST-<AREA>-NN` identifiers of [`engineering-style.md`](../engineering-style.md) §12.1 that
constrain this component's typing, async behaviour, errors, naming, layout, logging and
documentation, each with the one sentence that says how it applies *here*. Cite; never restate.

## 10. Testing strategy

The `ST-TST-*` rules that apply and what is specific here: the conformance suite this component
ships or passes, the doubles it needs, the typing tests of its public contract, the properties worth
a property-based test.

## 11. Open questions

Things this document does not settle, each with the ticket that will.
