# PR 03 — T1/T2 Read-Only MCP Sources and T3 Data-Quality Gate

```text
You are working on PR 03 of the DragonWings PAP Agentic Automation MVP v4.

BRANCH
feature/03-mcp-grounding-sources

GOAL
Implement grounded source acquisition through MCP.

Lesson: **MCP solves integration; T3 establishes trust**.

RULE
Do not invent real DragonWings CAN IDs, serial frames, registers, site limits, or provider credentials.

TELEMETRY MCP
Expose read-only tools/resources such as get_current_telemetry().
Fixture/replay implementation only.
Include source, source timestamp, schema/version, provenance, missing/error status.
No write/control tool.

WEATHER/SOLAR MCP
Expose read-only forecast acquisition using deterministic fixtures.
Keep future provider details behind the MCP boundary.

PAP CLIENT INTEGRATION
T1/T2 adapters call MCP and map responses into typed domain records.
Keep transport details out of domain logic.

POSTGRESQL
Persist sanitized source observations and provenance before/with validation.

T3
Validate freshness, required fields, ranges, units, impossible states represented by schema, source availability, and mixed-time/contradictory observations.

FAIL CLOSED
- unavailable != zero;
- never invent missing values;
- stale/invalid evidence cannot proceed as valid.

API
GET /api/v1/evidence/current?scenario=<name>

TEST
- normal;
- stale;
- missing;
- malformed;
- timeout/unavailable;
- schema mismatch;
- persistence/provenance;
- prove no write/control MCP tool exists.

PLAYWRIGHT
Run live local MCP servers plus PAP service and verify normal/stale/missing flows.

DOCUMENT
docs/lessons/03-mcp-ground-before-reasoning.md.

SPECIAL
Use `mcp-contract-safety`.

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
