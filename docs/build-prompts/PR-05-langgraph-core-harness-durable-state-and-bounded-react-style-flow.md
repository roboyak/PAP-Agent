# PR 05 — LangGraph Core Harness, Durable State, and Bounded ReAct-Style Flow

```text
You are working on PR 05 of the DragonWings PAP Agentic Automation MVP v4.

BRANCH
feature/05-langgraph-core-harness

GOAL
Introduce LangGraph as the top-level PAP harness.

Lesson: **the graph is the control plane; agents are optional nodes inside it**.

Do not introduce a live LangChain agent yet. First prove state, routing, persistence, retries, and safe termination deterministically.

STATE
Create typed serializable PAPGraphState containing IDs/status only where practical:
- episode/thread id;
- goal;
- source/evidence record IDs;
- validation status;
- forecast/calculation/constraint IDs;
- retry counters;
- fallback;
- reasoning mode;
- stop reason/status.

Do not duplicate large canonical domain records into checkpoint state unnecessarily.

GRAPH
Create explicit nodes:
- acquire_telemetry
- acquire_weather
- validate_evidence
- forecast
- calculate_availability
- validate_candidate
- finalize_episode

Use conditional edges for:
- valid/invalid;
- retry/fallback/stop;
- pass/reject.

Express the prior ReAct-like observe/assess/act/observe/revise-or-validate loop as explicit graph control.

BUDGETS
- max steps;
- bounded source retries;
- duplicate refresh suppression;
- no T4/T5 before T3-valid evidence;
- hard stop on unrecoverable invalid state.

CHECKPOINTING
Use the official LangGraph PostgreSQL checkpointer.
Keep checkpoint data logically separate from domain records.
Use in-memory saver for unit tests where persistence is not under test.
Use PostgreSQL saver for integration/runtime durable-execution tests.
Use the checkpointer's supported setup/initialization path rather than hand-authoring internal tables.

IDEMPOTENCY
Persist/create operations must remain safe under resume/replay.

TRACE API
GET /api/v1/episodes/{episode_id}
Return node/action summaries, evidence/result IDs, retries, validation, and stop reason.
Never expose private chain-of-thought.

TEST
- happy path;
- stale/source failure;
- retry then success;
- retry exhausted;
- invalid candidate;
- checkpoint persists;
- resume does not duplicate records;
- no route skips T3/T6;
- all fixtures reach END.

PLAYWRIGHT
Verify live normal and failure graph traces.

DOCUMENT
docs/lessons/05-langgraph-harness.md.

SPECIAL
Use `langgraph-workflow-safety`; use `db-migration-safety` if persistence setup changes.

QUALITY HANDOFF — REQUIRED BEFORE STOP

- Run `make verify`.
- Update the current reusable lesson with `lesson-capture`.
- Run `pr-readiness`; resolve all BLOCKER/MAJOR findings.
- Run every specialized skill applicable to this PR:
  - `db-migration-safety`
  - `mcp-contract-safety`
  - `langgraph-workflow-safety`
  - `langchain-agent-boundary`
  - `observability-trace-safety`
- Run `hil-local-verification`; include exact copy/paste human test commands and expected results.
- Run `pr-description`; use the repository PR template.
- Leave all HUMAN-ONLY boxes unchecked.
- Never push, open, approve, merge, or tag remotely.

STOP
Return the local handoff report and stop before remote actions.
```
