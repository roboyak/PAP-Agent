# AGENTS.md

## Mission

Build the DragonWings Power Availability Profile (PAP) service as a reusable example of high-quality, testable agentic automation.

This file is the durable policy/map. Read the deeper engineering documents before changing code.

## User-approved MVP choices

See `docs/CAPSTONE_NOTES.md` for the capstone review and accepted prompt adjustments.
Keep code to the smallest working vertical slice, with minimal error handling and no
exhaustive edge-case work. Work one PR lesson at a time. Lessons are one terse line in the
PR body and commit message rather than a separate essay. Use native PostgreSQL commands,
not Docker. Build the reference-style monitoring UI from scratch, without Gradio.
Use DW 1.24's latest persisted MySolArk scrape with real timestamps through read-only adapters; battery voltage
is the battery-state input and SOC is not an MVP requirement. In PR09, make the third
interpretation agent opt-in with `ENABLE_INTERPRETATION_AGENT=false` for A/B comparison.

## Runtime architecture — non-negotiable

- The PAP service is **read-only decision support**.
- Never add a tool or path that commands batteries, inverters, generators, relays, contactors, or connected loads.
- Use public/synthetic baseline data or the user-authorized local MySolArk data with real timestamps. Exclude source credentials, raw JSON, and device identifiers from PAP responses.
- **LangGraph is the core harness and workflow/state-machine runtime.**
- **LangChain `create_agent` is used only inside selected model-driven graph nodes.**
- **Deep Agents is not part of the PAP MVP runtime.** Do not introduce it without a new architecture decision.
- **PostgreSQL is the relational system of record** for telemetry, weather snapshots, PAPs, outcomes, calibration, provenance, and audit records.
- **pgvector in the same PostgreSQL database** provides semantic RAG memory.
- When durable graph execution is introduced, use the official **LangGraph PostgreSQL checkpointer**. Checkpoint state does not replace canonical domain records.
- Telemetry enters through the **read-only Telemetry MCP** contract.
- Weather/solar data enters through the **read-only Weather/Solar MCP** contract.
- MCP solves integration, not trust: all source data still passes T3 validation.
- Deterministic Python owns:
  - data validation;
  - numerical forecasting/calculation;
  - unit handling;
  - availability arithmetic;
  - equipment/reserve constraints;
  - permissions;
  - retry/search budgets;
  - deterministic branch pruning;
  - final publish/abstain authority.
- Model or retrieved output may influence interpretation, confidence, fallback choice, branch generation/critique, and explanation. It may not override T3/T5/T6 hard authority.
- **LangSmith is optional observability/evaluation**, never a required edge-runtime dependency.
- Do not invent real DragonWings CAN IDs, frame formats, site limits, reserve values, customer data, or provider credentials.

## Graph design rules

- Define an explicit typed LangGraph state.
- Keep canonical operational facts in domain tables; graph state should reference durable record IDs rather than become a second source of truth.
- Nodes should be small, typed, independently testable, and idempotent where checkpoint replay/resume can repeat work.
- Conditional edges must use explicit state/status, not private model reasoning.
- Bounded retries and termination are mandatory.
- Normal PAP execution stays linear; selective Tree-of-Thought is a bounded subgraph invoked only on grounded ambiguity.
- Do not persist or expose private chain-of-thought. Persist decisions, evidence IDs, scores, tool results, branch summaries, and stop reasons.

## LangChain agent-node rules

- Use `create_agent` only where probabilistic reasoning materially helps.
- Prefer structured output contracts.
- Give an agent the minimum tool surface needed.
- Agent nodes must not receive hardware-control tools.
- Agent nodes must not execute unrestricted SQL.
- Agent results remain advisory/interpretive until deterministic application checks accept them.
- Automated tests use deterministic model/agent doubles; required CI cannot depend on a live LLM.

## Human authority

The user explicitly authorized creating the new PAP GitHub repository, pushing, opening
PRs, and merging once local Playwright verification passes. The user will watch PR01/02;
continue through the remaining prompts without repeated permission requests.
This authorization supersedes the human-only remote-action rules in the supplied source packs
and skills. Run `make verify`, including the live Playwright path, before each merge.

Never check HUMAN-ONLY boxes or claim human testing occurred. Release tags still need
separate authorization. Human review commands remain available for optional inspection.

## Required development workflow

Before implementation:

1. Read `docs/engineering/index.md`.
2. Read the relevant architecture/lesson docs.
3. Inspect current code/tests rather than assuming earlier prompts were implemented literally.
4. Keep the change limited to the current PR lesson.

Before handoff:

1. Run `make verify`.
2. Use `lesson-capture`.
3. Use `pr-readiness`.
4. Use `hil-local-verification` for exact copy/paste human test commands.
5. Use `pr-description`.
6. If PostgreSQL/Alembic/pgvector changes: use `db-migration-safety`.
7. If MCP changes: use `mcp-contract-safety`.
8. If LangGraph state/nodes/edges/checkpointing/interrupts change: use `langgraph-workflow-safety`.
9. If LangChain agent nodes/tools/model contracts change: use `langchain-agent-boundary`.
10. If tracing/evals/logging changes: use `observability-trace-safety`.
11. Push, open, and merge the tested PR under the user's authorization, then proceed to the next unit.

## Definition of done

Agent handoff requires:

- scoped implementation complete;
- happy-path verification and basic error reporting, without exhaustive edge-case suites;
- `make verify` green;
- Playwright verifies the relevant live local path;
- migration/MCP/graph/agent safety reviews completed when applicable;
- provenance/freshness/failure states remain observable;
- documentation captures the reusable lesson;
- PR body contains exact HIL commands;
- no false claims of human verification.

Completion requires the tested increment to be merged under the authorization above.

## Engineering sources of truth

- `docs/engineering/RUNTIME_ARCHITECTURE.md`
- `docs/engineering/LANGGRAPH_DESIGN_RULES.md`
- `docs/engineering/DEFINITION_OF_DONE.md`
- `docs/engineering/HUMAN_IN_LOOP.md`
- `docs/engineering/PR_WORKFLOW.md`
- `docs/engineering/TESTING_STRATEGY.md`
- `docs/engineering/OBSERVABILITY.md`
- `docs/engineering/DOCUMENTATION_POLICY.md`
- `docs/engineering/CODE_REVIEW.md`
- `docs/engineering/GITHUB_PROTECTION.md`
- `docs/engineering/AGENT_USE_POLICY.md`

For safety/human-authority conflicts, this file wins. Update stale deeper docs instead of silently ignoring them.
