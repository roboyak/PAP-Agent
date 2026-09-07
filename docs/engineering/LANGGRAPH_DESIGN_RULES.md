# LangGraph Design Rules

## State
- explicit typed state;
- serializable;
- reference durable records by ID;
- no hidden replacement for PostgreSQL domain tables.

## Nodes
Keep one clear responsibility:
- acquire telemetry;
- acquire weather;
- validate;
- retrieve;
- assess ambiguity;
- agent interpretation;
- forecast;
- calculate;
- hard validate;
- publish;
- evaluate.

## Edges
Route on explicit statuses, not free-form model prose.

## Checkpointing
- in-memory saver for unit tests unless persistence itself is under test;
- PostgreSQL checkpointer for durable runtime/integration paths;
- test resume before relying on it operationally.

## Idempotency
Nodes may re-enter after resume. Side effects must be idempotent/deduplicated.

## Interrupts
Optional for read-only MVP. If introduced:
- durable checkpointer required;
- validate human resume data;
- no private chain-of-thought in review payloads.

## ToT
Bounded subgraph:
- branch factor 3;
- beam width 2;
- depth 3;
- max model/reasoning calls 8;
- deterministic hard checks before model scoring;
- no valid branch -> lower confidence/abstain.
