# Definition of Done

## Agent handoff done
A branch may be handed to a human only when:

- scope complete;
- non-goals not pulled forward;
- the smallest happy path is verified with basic error reporting;
- `make verify` passes;
- Playwright covers the relevant live local path;
- specialized DB/MCP/LangGraph/LangChain/observability reviews were run when applicable;
- provenance/freshness/failure state remains visible;
- lesson/docs are current;
- PR body includes exact HIL commands;
- HUMAN-ONLY boxes remain unchecked unless a human supplies the signoff.

## PR done
The user authorized agent push/PR/merge after local Playwright verification.
A PR is done when its narrow implementation passes `make verify`, has a terse lesson,
and is merged. Optional human checks are not represented as completed by the agent.
