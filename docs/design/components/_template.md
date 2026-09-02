# <Component name>

_Status: not started | in progress (#ticket) | reviewed._
_Layer: core | adapter | plugin | testing._
_ADRs: ADR-XXXX, ADR-YYYY. Research: `docs/research/NN`._

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

Invariants that must always hold; what happens on timeout, cancellation, dependency outage, bad
input, concurrent use; what is logged (never message text, tokens or PII) and what is surfaced to
observability.

## 9. Typing and async rules

Generics, Protocols, `Final`s, sentinel handling; blocking calls forbidden; how cancellation is
handled; sync face (if any) and how it is produced.

## 10. Testing strategy

Unit, contract (shared suites for pluggable implementations), integration (mock server / in-memory
transport), property-based where invariants are compact, typing tests for the public contract.

## 11. Open questions

Things this document does not settle, each with the ticket that will.
