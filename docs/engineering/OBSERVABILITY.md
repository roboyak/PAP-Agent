# Observability

The main Recorded day view explains actual solar, site use and leftover solar from completed
publication evidence in Pacific time. Missing/stale samples are gaps, never zero-filled;
future hours stay blank. Future estimate is a separate baseline view. Inspector retains
all six tabs and the fixed episode behind either view; raw records keep their original timestamps.

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

Calibration maintenance records the settings hash, recent/prior outcome IDs and sample counts,
error means, drift availability, escalation signals and configured review date. The saved
run's assessment remains fixed; Inspector's current-maintenance check is labeled separately.
Review age and live feedback expiry are explicit. Qualitative confidence has no ECE value;
error-mean drift is not presented as a formal distribution-shift test.
