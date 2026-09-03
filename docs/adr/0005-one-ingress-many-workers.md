---
status: accepted
date: 2026-09-03
ticket: "#13"
---

# A bot scales as one event ingress and many workers, never as identical replicas

Every WebSocket connection of a bot account receives every event (`docs/research/01`), so a
second identical replica processes each message twice. We decided the deployment model is
**one WebSocket consumer per bot**, a **horizontally replicable webhook ingress**, and **heavy
work offloaded to workers** (any task system) through the Runtime's sync or async face. Handlers
therefore stay thin and fast, and every process declares its role explicitly instead of inferring
it from configuration.

## Consequences

- Process roles, the single-consumer guard and the deployment view are designed in #19 and #40.
- Distributed processing via brokers stays a recipe, not a Core capability (ADR-0002).
