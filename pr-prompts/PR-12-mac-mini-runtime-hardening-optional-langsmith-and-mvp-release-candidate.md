# PR 12 — Mac mini Runtime Hardening, Optional LangSmith, and MVP Release Candidate

```text
You are working on PR 12 of the DragonWings PAP Agentic Automation MVP v4.

BRANCH
feature/12-mac-mini-runtime

GOAL
Turn the prototype into a safe local Mac mini MVP runtime.

Lesson: **production-quality agentic automation requires explicit process boundaries, readiness, durable state, budgets, observability, and safe failure**.

NO HARDWARE CONTROL.

RUNTIME PROFILES
- test
- development
- macmini-replay
No production-control profile.

POSTGRESQL/PGVECTOR
Document/automate one supported local Mac mini deployment path.
Readiness:
- reachable;
- migrations current;
- pgvector enabled;
- semantic query succeeds;
- writable.

LANGGRAPH
- PostgreSQL checkpointer initialized;
- graph compiles;
- readiness can create/read a safe checkpoint or equivalent supported health operation;
- max steps/retries/ToT budgets configured;
- resume behavior tested.

MCP
Run local read-only:
- Telemetry MCP;
- Weather/Solar MCP.

macmini-replay uses synthetic/replay implementations.
Readiness verifies schemas/versions and confirms no write/control tool exists.

PAP SERVICE
FastAPI/operator service on loopback.
T1/T2 call MCP.
T3-T8 deterministic/application nodes.
T9 PostgreSQL/pgvector.
LangChain agent nodes only where defined.
Selective ToT only when ambiguity trigger fires.

LOCAL PATHS
User-writable logs/replay/PAP exports.
No second vector database.

SERVICE LIFECYCLE
Provide:
- scripts/bootstrap_mac.sh
- scripts/run_local.sh
- scripts/verify_local.sh
- documented launchd templates/generator or an equivalent lightweight supervisor strategy
- disable/uninstall instructions.

Avoid root unless necessary.

HEALTH
- /health/live
- /health/ready

Ready requires:
- PostgreSQL/pgvector;
- graph/checkpointer;
- Telemetry MCP;
- Weather MCP;
- config;
- replay/source data;
- no forbidden control tools.

AUDIT
Structured local logs:
- PAP ID;
- episode/thread ID;
- graph node;
- agent node;
- MCP request/source ID;
- retrieval IDs;
- ToT branch/score/prune;
- validation;
- stop reason.

LANGSMITH
Optional development/evaluation integration.
Disabled/non-blocking by default on edge.
Trace failure never fails PAP.
No secrets/private chain-of-thought.

ONE-COMMAND LOCAL DEMO
- DB up/check;
- migrate;
- seed synthetic relational + semantic data;
- start MCP servers;
- start PAP service;
- normal scenario;
- stale scenario;
- RAG A/B;
- ToT ambiguity;
- print PAP IDs/statuses;
- clean stop.

UI
Banner:
READ-ONLY MVP — SYNTHETIC/REPLAY DATA

Show readiness and latest reasoning mode/PAP.

VERIFY
make verify includes:
- format/lint;
- migrations;
- unit;
- integration;
- MCP contract;
- pgvector;
- LangGraph transitions/checkpoint/resume;
- LangChain fake-agent tests;
- Playwright;
- startup readiness.

Add safe `make verify-mac`.

DOCS
- docs/MVP_RUNBOOK.md
- docs/architecture/FINAL_MVP.md
- docs/lessons/12-agentic-automation-baseline.md

FINAL_MVP must state:
- LangGraph harness;
- LangChain bounded agent nodes;
- PostgreSQL/pgvector;
- MCP boundaries;
- deterministic T3/T5/T6;
- selective ToT;
- optional LangSmith;
- Deep Agents excluded from MVP;
- all synthetic assumptions;
- requirements before real telemetry/weather integration.

REAL SOURCE NOTE
The capstone does not specify actual CAN IDs, framing, site limits, or final weather-provider credentials/contracts.
Keep source servers replay/fixture implementations and document sanitized contracts required for future integration.
Do not guess.

Suggest but DO NOT create/push:
v0.1.0-mvp

SPECIAL
Use every relevant specialized safety skill.

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
