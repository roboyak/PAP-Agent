# Architecture Decision v4 — LangGraph-Centered PAP Runtime

## Status
Accepted for MVP baseline.

## Decision

Use:
- LangGraph as workflow/state-machine harness;
- LangChain `create_agent` inside selected reasoning nodes;
- PostgreSQL as relational system of record;
- pgvector in PostgreSQL for RAG memory;
- LangGraph PostgreSQL checkpointer for durable workflow state;
- MCP for read-only Telemetry/Weather integration;
- deterministic Python for validation/calculation/constraints/budgets/hard pruning/publish-abstain authority;
- LangSmith optionally for traces/evals;
- no Deep Agents in PAP MVP.

## Rationale

The PAP design is primarily a stateful deterministic/agentic workflow with explicit failure paths, retrieval, bounded branching, and auditable durable state. LangGraph naturally represents that architecture. LangChain agents provide bounded probabilistic reasoning without owning the control plane.
