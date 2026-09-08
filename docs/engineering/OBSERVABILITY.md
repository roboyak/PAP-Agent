# Observability

## Required local observability
The Mac mini must remain diagnosable with LangSmith disabled.

Correlate:
- PAP ID;
- episode / LangGraph thread ID;
- graph node/state transition;
- MCP request/source IDs;
- PostgreSQL evidence IDs;
- retrieval selected/rejected IDs;
- agent-node status;
- ToT scores/prune reasons;
- T6 validation;
- stop reason.

The replay simulator adds a simulation ID, selected wing/window/cadence, completed-step count
and current status. Its Results list links each time step to its canonical episode and PAP.
Inspector stays fixed on that episode while the simulator continues. Valid/withheld counts
measure workflow outcomes, not forecast accuracy; overlapping twelve-hour predictions are
not added into a weekly energy figure. Model inputs and budgets remain visible per episode.

## LangSmith
Optional for development/evaluation.

Rules:
- opt-in/configurable;
- edge correctness independent of it;
- trace failure non-fatal;
- no secrets/private chain-of-thought;
- synthetic/test traces labeled.

## Evaluation
Keep distinct:
1. source quality;
2. T3 validation;
3. retrieval quality;
4. deterministic calculation;
5. LangChain agent quality;
6. ToT search;
7. final PAP behavior.
