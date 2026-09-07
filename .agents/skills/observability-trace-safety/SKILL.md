---
name: observability-trace-safety
description: Review structured logs, LangGraph traces, optional LangSmith instrumentation, metrics, and evaluation for safety and edge independence.
---

# Observability and Trace Safety

Required local evidence:
- episode/thread ID;
- graph node;
- MCP request/source ID;
- tool invocation;
- PAP ID;
- retrieval result IDs;
- ToT branch IDs/scores/prune reasons;
- validation and stop reason;
- model timing/token metadata when available.

LangSmith, if enabled:
- opt-in/configurable;
- correctness does not depend on it;
- trace-export failure is non-fatal;
- scrub secrets/private data;
- never export private chain-of-thought;
- label synthetic/test traces.

Evaluate separately:
- source/data quality;
- retrieval;
- deterministic forecast/calculation;
- agent-node quality;
- ToT search quality;
- final PAP behavior.
