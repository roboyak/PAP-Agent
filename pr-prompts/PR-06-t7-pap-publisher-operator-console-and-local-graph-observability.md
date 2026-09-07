# PR 06 — T7 PAP Publisher, Operator Console, and Local Graph Observability

```text
You are working on PR 06 of the DragonWings PAP Agentic Automation MVP v4.

BRANCH
feature/06-pap-publisher-console

GOAL
Add structured publication, human-visible local operation, and local graph observability.

Lesson: **an agentic workflow is only trustworthy when outputs and control flow are inspectable**.

T7 PUBLISHER
Publish only:
- T6-validated PAP, or
- typed insufficient_data / insufficient_confidence outcome.

Canonical PAP JSON:
- profile id;
- generated_at;
- horizon;
- intervals;
- confidence;
- freshness;
- constraints;
- evidence/provenance;
- validation results;
- explanation;
- episode/thread id.

Persist PAP/interval/evidence links in PostgreSQL.

GRAPH
Add publish/finalize nodes to the LangGraph flow.
Ensure publishing is idempotent under checkpoint replay.

API
- POST /api/v1/pap/run?scenario=<name>
- GET /api/v1/pap/latest
- GET /api/v1/pap/{id}
- GET /api/v1/episodes/{id}

UI
Minimal operator console:
- READ ONLY;
- synthetic/replay mode;
- latest PAP;
- current freshness;
- interval table;
- confidence;
- constraints;
- provenance;
- graph node/stop summary;
- trace link.

LOCAL OBSERVABILITY
Structured logs correlate:
- PAP id;
- episode/thread id;
- graph node;
- MCP source IDs;
- validation/stop reason.

LANGSMITH
Optional only.
If added now, make it disabled by default/non-blocking and use official tracing integration.
The edge runtime must remain correct without it.

PLAYWRIGHT
- normal scenario renders PAP/provenance;
- stale scenario renders insufficient state;
- trace shows route/stop reason;
- no private chain-of-thought displayed;
- no fabricated power shown as valid.

TEST
Publisher refuses unvalidated candidates and remains idempotent on replay.

DOCUMENT
docs/lessons/06-structured-publication-observability.md.

SPECIAL
Use `langgraph-workflow-safety` and `observability-trace-safety`.

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
