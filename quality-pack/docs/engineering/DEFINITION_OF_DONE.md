# Definition of Done

## Agent handoff done
A branch may be handed to a human only when:

- scope complete;
- non-goals not pulled forward;
- success and important failure/abstention tests exist;
- `make verify` passes;
- Playwright covers the relevant live local path;
- specialized DB/MCP/LangGraph/LangChain/observability reviews were run when applicable;
- provenance/freshness/failure state remains visible;
- lesson/docs are current;
- PR body includes exact HIL commands;
- HUMAN-ONLY boxes remain unchecked;
- no remote action was performed.

## PR done
Only after a human:
1. reviews the diff;
2. runs HIL locally;
3. confirms expected behavior;
4. completes HUMAN-ONLY signoff;
5. opens/reviews the PR;
6. performs final merge.
