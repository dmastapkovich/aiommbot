---
status: accepted
date: 2026-09-03
ticket: "#13"
---

# A bot scales as one WebSocket consumer, replicated Webhook processes and many workers, never as identical replicas

Every WebSocket connection of a bot account receives every event (`docs/research/01`), so a
second identical replica processes each message twice. We decided the deployment model is
**one WebSocket consumer per bot**, **horizontally replicated Webhook processes**, and **heavy
work offloaded to workers** (any task system) through the Workspace, synchronous or asynchronous (ADR-0029). Handlers
therefore stay thin and fast, and every process declares its role explicitly instead of inferring
it from configuration.

## Consequences

- Process roles are the ProcessProfile (ADR-0016), the single-consumer guard is ADR-0023, and the
  deployment shapes are §7 of the architecture document.
- Distributed processing via brokers stays a recipe, not a Core capability (ADR-0002).
