# PR 09 — RAG Quality Controls and Grounded LangChain Interpretation Node

```text
You are working on PR 09 of the DragonWings PAP Agentic Automation MVP v4.

BRANCH
feature/09-rag-quality-grounded-agent

GOAL
Add retrieval-quality controls and introduce the first bounded LangChain `create_agent` node.

Lesson: **retrieval and generation are separate reliability layers; an agent node remains bounded by the graph**.

RETRIEVAL PIPELINE
- retrieve 5;
- metadata/validity filters;
- configurable minimum score;
- rerank;
- deduplicate near-duplicates where practical;
- inject at most top 3;
- preserve source/date/provenance;
- record query, filters, candidate IDs/scores, selected/rejected reasons, retrieval status.

LANGCHAIN AGENT NODE
Create a `grounded_interpretation` node using `create_agent`.

Purpose:
- interpret retrieved evidence;
- recommend confidence adjustment;
- recommend documented fallback/re-evaluation guidance;
- generate a concise grounded explanation.

Structured output must include:
- evidence IDs used;
- confidence adjustment recommendation within bounded enum/range;
- optional documented fallback ID;
- re-evaluation recommendation;
- explanation;
- insufficiency flag.

TOOLS
Give the agent no hardware tools and no unrestricted SQL.
Prefer passing selected evidence in node input rather than letting it roam.
If tools are necessary, use only bounded read-only approved tools.

DETERMINISTIC GATE
Application code validates the structured recommendation.
The agent cannot:
- rewrite T5 available power;
- bypass T6;
- invent evidence;
- create site policy.

LANGGRAPH
Add explicit route:
retrieve -> grounded_interpretation -> deterministic recommendation validator -> continue.
If agent fails/malformed/times out, safely continue without its adjustment, lower confidence, or abstain according to explicit policy.

A/B FIXTURE
rapid cloud + low SOC + elevated wind with similar validated prior solar overestimation.

Without retrieval/agent:
baseline physically valid PAP.

With retrieval/agent:
same deterministic available power;
possibly lower confidence;
recommend re-evaluation before optional load;
visible provenance.

FAILURE FIXTURE
Wrong configuration/expired memory must be filtered out.

TEST
- retrieval separately from final PAP;
- agent structured output with deterministic fake model;
- malformed/model failure;
- agent cannot alter T5/T6 result;
- wrong memory excluded;
- same physical result in A/B.

PLAYWRIGHT
Expose A/B result:
same calculated availability, changed bounded confidence/guidance, evidence IDs visible.

DOCUMENT
docs/lessons/09-rag-and-bounded-agent-nodes.md.

SPECIAL
Use `langchain-agent-boundary`, `langgraph-workflow-safety`, and `observability-trace-safety`.

QUALITY HANDOFF — REQUIRED BEFORE STOP

- Run `make verify`.
- Update the current reusable lesson with `lesson-capture`.
- Run `pr-readiness`; resolve all BLOCKER/MAJOR findings.
- Run every specialized skill applicable to this PR:
  - `db-migration-safety`
  - `mcp-contract-safety`
  - `langgraph-workflow-safety`
  - `langchain-agent-boundary`
  - `observability-trace-safety`
- Run `hil-local-verification`; include exact copy/paste human test commands and expected results.
- Run `pr-description`; use the repository PR template.
- Leave all HUMAN-ONLY boxes unchecked.
- Never push, open, approve, merge, or tag remotely.

STOP
Return the local handoff report and stop before remote actions.
```
