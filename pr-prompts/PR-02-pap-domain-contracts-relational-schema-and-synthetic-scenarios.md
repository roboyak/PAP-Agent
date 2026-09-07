# PR 02 — PAP Domain Contracts, Relational Schema, and Synthetic Scenarios

```text
You are working on PR 02 of the DragonWings PAP Agentic Automation MVP v4.

BRANCH
feature/02-pap-domain-contracts

GOAL
Define typed domain state and relational persistence before orchestration.

Lesson: **typed state and auditable storage before agent behavior**.

Create typed models for:
- TelemetrySnapshot
- WeatherForecastInterval
- ReservePolicy
- ForecastInterval
- PowerAvailabilityInterval
- PAP
- AgentEpisodeRecord
- provenance/validation status structures

Use explicit units and timezone-aware timestamps.

POSTGRESQL
Create normalized migrations/tables/repositories.
Use JSONB only for bounded extensible metadata.
Add appropriate indexes/foreign keys.
Do not manually create LangGraph checkpointer tables; that arrives with PR05.

FIXTURES
Synthetic/public:
- normal sunny;
- rapidly changing cloud;
- low SOC;
- elevated wind;
- stale telemetry;
- missing field;
- contradictory sources.

Never imply fixture values are real DragonWings limits.

Fixture loading must be idempotent through repositories.

API
Development-only scenario list/detail endpoints.

TEST
- serialization/validation;
- invalid ranges;
- timezone behavior;
- repository round trips;
- migration from empty DB;
- idempotent fixtures;
- API contracts.

PLAYWRIGHT
Read a persisted fixture through the live API.

DOCUMENT
docs/lessons/02-explicit-domain-state.md.

NON-GOALS
No LangGraph graph, LangChain agent, RAG behavior, calculations, or real source integration.

SPECIAL
Use `db-migration-safety`.

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
