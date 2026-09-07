---
name: hil-local-verification
description: Create the human-in-the-loop local verification procedure for a PR, with exact copy/paste commands, expected results, failure behavior, and human-only signoff.
---

# Human-in-the-Loop Local Verification

Create a reproducible manual test plan.

## Required sections

### Preconditions
Only prerequisites actually required.

### Copy/paste commands

Provide one fenced `bash` block runnable from repo root.

Normally begin with repository-valid equivalents of:

```bash
git status --short
git branch --show-current
make setup
make db-up
make migrate
make verify
```

Then include PR-specific commands for:
- launching local services;
- MCP inspection;
- `curl`;
- targeted pytest;
- Playwright;
- PostgreSQL/pgvector inspection;
- LangGraph trace/checkpoint inspection;
- RAG A/B;
- ToT route when relevant.

Never list a command that does not exist.

### Expected results
State the exact observable behavior for each PR-specific step.

Include:
- success behavior;
- important failure/abstention behavior;
- provenance/freshness;
- read-only/no-control confirmation;
- graph route/stop reason when relevant.

### Human inspection
List UI/API/log/database/trace evidence to inspect manually.

### HUMAN-ONLY signoff

Leave all unchecked:

- [ ] **HUMAN ONLY:** I ran the commands above on my local system.
- [ ] **HUMAN ONLY:** The observed results matched the expected results.
- [ ] **HUMAN ONLY:** I reviewed the branch diff and found no unexplained changes.
- [ ] **HUMAN ONLY:** I verified the service remains read-only and no hardware-control action was introduced.
- [ ] **HUMAN ONLY:** I approve this PR for GitHub submission/merge.

Never claim a human ran a command.
