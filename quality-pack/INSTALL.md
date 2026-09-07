# Install the v4 Codex Quality Pack

Copy this pack into repository root **before PR 01**.

Expected:
```text
AGENTS.md
.codex/config.toml
.codex/agents/*.toml
.agents/skills/*/SKILL.md
.github/PULL_REQUEST_TEMPLATE.md
docs/engineering/*
docs/lessons/README.md
scripts/pre_pr_verify.sh
```

Start a fresh Codex session and ask it to summarize, without changes:

- LangGraph = harness/state machine;
- LangChain create_agent = selected agent nodes;
- Deep Agents = not MVP;
- PostgreSQL = system of record;
- pgvector = RAG;
- PostgreSQL LangGraph checkpointer = durable graph state;
- read-only Telemetry/Weather MCP;
- deterministic T3/T5/T6 authority;
- optional LangSmith;
- human-only push/PR/merge authority.

If correct, run PR 01 from the v4 prompt series.
