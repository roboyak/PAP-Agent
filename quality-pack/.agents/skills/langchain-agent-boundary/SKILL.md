---
name: langchain-agent-boundary
description: Review any LangChain create_agent node, model configuration, tools, middleware, or structured-output contract before handoff.
---

# LangChain Agent Boundary

Ask first: why is an agent needed here?

Check:

1. Inputs are minimal and preserve evidence/provenance IDs.
2. Output is structured and schema-validated.
3. No private chain-of-thought is stored.
4. Tool surface is minimum-necessary:
   - no hardware control;
   - no unrestricted SQL;
   - MCP tools remain read-only.
5. T3/T5/T6 remain authoritative.
6. Model timeout/retry/iteration/token budgets are bounded where possible.
7. Malformed/unavailable model output fails closed.
8. Automated tests use deterministic model/agent doubles.
9. Tests prove an agent cannot bypass deterministic checks.

Agent autonomy is never a reason to weaken graph-owned permissions or termination.
