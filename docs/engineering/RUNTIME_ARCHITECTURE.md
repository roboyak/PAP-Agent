# PAP Runtime Architecture — v4

## Decision

- **LangGraph** — top-level stateful workflow harness.
- **LangChain `create_agent`** — selected model-driven nodes.
- **PostgreSQL** — relational system of record.
- **pgvector** — semantic RAG memory in PostgreSQL.
- **LangGraph PostgreSQL checkpointer** — durable workflow execution state.
- **MCP** — read-only Telemetry and Weather/Solar boundaries.
- **Deterministic Python** — validation, numerical work, constraints, budgets, hard pruning, publish/abstain authority.
- **LangSmith** — optional traces/evals.
- **Deep Agents** — intentionally excluded from PAP MVP.

```mermaid
flowchart TD
    UI[FastAPI / Operator UI] --> G[LangGraph PAP StateGraph]
    G --> TM[Telemetry MCP]
    G --> WM[Weather / Solar MCP]
    TM --> PG[(PostgreSQL)]
    WM --> PG
    PG --> T3[T3 Validate]
    T3 -->|invalid| X[Insufficient data]
    T3 -->|valid| R{Need retrieval?}
    R -->|yes| V[T9 pgvector]
    R -->|no| A{Ambiguous?}
    V --> A
    A -->|no| L[Linear route]
    A -->|yes| TOT[Selective ToT subgraph]
    L --> T4[T4 Forecast]
    TOT --> T4
    T4 --> T5[T5 Availability]
    T5 --> T6[T6 Hard Validation]
    T6 -->|reject| Y[Lower confidence / abstain]
    T6 -->|pass| T7[T7 Publish]
    T7 --> T8[T8 Evaluate]
    T8 --> PG
    G -. optional .-> LS[LangSmith]
```

## Persistence separation

### Domain tables
Canonical telemetry, weather, forecasts, PAPs, outcomes, calibration, provenance.

### pgvector semantic records
Approved semantic representations for RAG.

### LangGraph checkpoints
Execution snapshots for durable resume/HITL/debugging.

A checkpoint never replaces a canonical domain record.

## Agent nodes

Use LangChain agents only for:
- grounded interpretation;
- ToT candidate generation;
- qualitative critique;
- explanation.

They do not own arithmetic, constraints, permissions, or final safety.
