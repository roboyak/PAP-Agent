# Testing Strategy

## Unit
- domain validation;
- T3/T4/T5/T6 deterministic logic;
- graph routing predicates;
- budgets/scoring;
- pure transforms.

## PostgreSQL / pgvector integration
- migrations from zero and prior revision;
- repositories;
- provenance relations;
- pgvector search/filter;
- embedding version/dimension.

## MCP integration
- normal;
- stale;
- malformed;
- unavailable/timeout;
- schema mismatch;
- read-only tool surface.

## LangGraph integration
- graph compile;
- expected routes;
- failure routes;
- bounded retries;
- checkpoint persistence;
- resume/idempotency;
- interrupts when introduced;
- ToT budgets.

## LangChain agent nodes
Required tests use deterministic model/agent doubles.
Test structured output, tool allowlists, malformed output, model failure, deterministic-authority rejection.

## Playwright
Exercise a live local PAP service:
- valid PAP;
- stale/insufficient;
- provenance;
- RAG A/B;
- selective ToT;
- read-only status.

## HIL
Every PR has one success and one important failure/abstention scenario with exact commands.

Required automated tests do not depend on real hardware, paid APIs, live nondeterministic LLM output, or LangSmith availability.
