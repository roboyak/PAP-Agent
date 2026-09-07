# Code Review

## BLOCKER
- hardware-control path;
- write-capable source MCP;
- T3/T5/T6 bypass;
- unsafe/unbounded graph;
- data loss/corruption risk;
- secrets/sensitive data;
- fail-open critical path;
- required verification cannot run.

## MAJOR
- likely regression;
- missing failure handling;
- lost provenance/freshness;
- unsafe agent tool scope;
- significant checkpoint/resume issue;
- meaningful test/doc gap.

## MINOR
Non-blocking maintainability/readability/docs issue.

Review behavior before style.
