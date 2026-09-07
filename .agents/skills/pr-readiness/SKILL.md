---
name: pr-readiness
description: Run before handing any PAP branch to a human. Executes the full local gate, delegates independent read-only review, reconciles findings, and blocks handoff when correctness, safety, graph workflow, testing, docs, database, MCP, or agent-boundary issues remain.
---

# PR Readiness

1. Confirm branch and diff:
   ```bash
   git status --short
   git branch --show-current
   git diff --stat main...HEAD
   ```

2. Read `AGENTS.md`, Definition of Done, Code Review, and the current lesson.

3. Run:
   ```bash
   make verify
   ```

4. Delegate read-only review in parallel:
   - `pr_reviewer`
   - `test_auditor`
   - `architecture_reviewer`
   - `workflow_reviewer`
   - `safety_reviewer`
   - `docs_reviewer`

5. Classify and reconcile:
   - **BLOCKER**: unsafe control, deterministic-authority bypass, unsafe/unbounded graph, corrupt migration, untested critical failure, broken verification.
   - **MAJOR**: likely regression, weak provenance/validation, unsafe agent tool scope, missing checkpoint/resume safety, meaningful test/doc gap.
   - **MINOR**: non-blocking maintainability/docs issue.

6. Fix all BLOCKER and MAJOR findings.

7. Use specialized skills as applicable:
   - `db-migration-safety`
   - `mcp-contract-safety`
   - `langgraph-workflow-safety`
   - `langchain-agent-boundary`
   - `observability-trace-safety`

8. Re-run `make verify`.

9. Use:
   - `hil-local-verification`
   - `pr-description`
   - `lesson-capture`

10. Final handoff must say:

   **HUMAN TESTING REQUIRED — NOT READY TO MERGE UNTIL HUMAN SIGNOFF.**

Do not push, open a remote PR, approve, merge, tag, or check HUMAN-ONLY boxes.
