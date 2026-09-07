---
name: pr-description
description: Draft a DragonWings PAP PR description including architecture impact, exact automated evidence, HIL commands, risks, rollback, docs, and human-only merge gates.
---

# PR Description

Use `.github/PULL_REQUEST_TEMPLATE.md`.

Document:
- reusable architectural lesson;
- scope/non-goals;
- LangGraph state/node/edge/checkpoint impact;
- LangChain create_agent node/tool/structured-output impact;
- PostgreSQL/Alembic/pgvector;
- MCP;
- deterministic authority;
- optional LangSmith;
- exact automated commands actually run;
- exact HIL commands from `hil-local-verification`;
- risks/limitations;
- rollback;
- docs changed.

Leave every HUMAN-ONLY checkbox unchecked.

Never claim "human verified", "approved", or "safe to merge" unless the human explicitly provided that fact.

Final status:

**Status: automated checks complete; HUMAN LOCAL VERIFICATION AND MERGE APPROVAL PENDING.**
