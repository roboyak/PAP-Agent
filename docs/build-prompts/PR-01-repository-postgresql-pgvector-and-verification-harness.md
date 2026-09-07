# PR 01 — Repository, PostgreSQL/pgvector, and Verification Harness

```text
You are working on PR 01 of the DragonWings PAP Agentic Automation MVP v4.

BRANCH
feature/01-agentic-service-foundation

GOAL
Create the smallest runnable repository, PostgreSQL/pgvector persistence foundation, and local verification harness.

Lesson: **harness and durable infrastructure before intelligence**.

IMPLEMENT
1. Python src-layout package.
2. Minimal FastAPI service.
3. GET /health and GET /api/v1/version.
4. Typed settings with DATABASE_URL and safe local defaults.
5. PostgreSQL repository/session layer.
6. Alembic migrations; enable pgvector extension explicitly.
7. Real DB health query.
8. Reproducible local PostgreSQL+pgvector development path; pinned Compose/container is acceptable.
9. Minimal `/` page with DragonWings PAP Forecaster, READ ONLY, synthetic/local mode.
10. pyproject dependencies only for this increment.
11. pytest for health/version/config/database.
12. Playwright Python live-service smoke test.
13. Make targets: setup, db-up, db-down, migrate, dev, format, format-check, lint, test, e2e, verify.
14. .env.example and .gitignore.
15. Keep the existing quality/governance files intact.
16. docs/lessons/01-agentic-harness.md.

ARCHITECTURE
Do not add Deep Agents.
Do not add another vector database.
Application LangGraph/LangChain behavior is intentionally deferred.

ACCEPTANCE
- fresh setup documented;
- DB reachable;
- pgvector enabled;
- migrations from empty DB succeed;
- service loopback only;
- no required external cloud service;
- Playwright passes;
- make verify passes.

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
