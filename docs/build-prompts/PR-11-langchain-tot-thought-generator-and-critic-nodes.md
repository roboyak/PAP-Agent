# PR 11 — LangChain ToT Thought Generator and Critic Nodes

```text
You are working on PR 11 of the DragonWings PAP Agentic Automation MVP v4.

BRANCH
feature/11-langchain-tot-agent-nodes

GOAL
Replace deterministic ToT candidate/critic fixtures with bounded LangChain `create_agent` nodes while keeping deterministic beam control.

Lesson: **generation and critique can be probabilistic; selection authority and hard pruning remain deterministic**.

THOUGHT GENERATOR AGENT NODE
Input:
- same validated state for sibling candidates;
- same selected pgvector evidence;
- branch-history summary.

Structured output up to 3 candidate thoughts.
Each must:
- list evidence IDs;
- state uncertainty/fallback implications;
- avoid unsupported critical assumptions;
- never propose hardware control.

CRITIC AGENT NODE
Receives structured candidate + evidence + deterministic tool results.

Hard checks happen BEFORE the critic:
- stale/invalid required data;
- equipment-limit violation;
- reserve violation;
- unsupported critical assumption detectable from contracts/provenance.

Only survivors reach critic.

Critic structured rubric:
- grounding/provenance: 25
- freshness/source agreement: 20
- forecast consistency: 20
- uncertainty calibration: 20
- operational usefulness: 15

Critic cannot override hard failures.

OPTIONAL DECISION-ADVISOR AGENT
May compare close surviving candidates and return structured recommendation.
It is advisory only.

DETERMINISTIC BEAM CONTROLLER
- beam 2;
- branch factor 3;
- depth 3;
- max model calls 8;
- within 5 points prefer stronger provenance/lower uncertainty or keep both if beam permits;
- early terminate only if hard checks pass, score >= 80, lead >= 10;
- at depth limit choose best valid or lower confidence/abstain.

LANGGRAPH
Use agent nodes inside the ToT subgraph.
Keep graph topology and deterministic controller independent of model provider.

TEST
Use deterministic fake models:
- fluent invalid candidate hard-pruned before critic;
- structured-output validation;
- malformed generator/critic output;
- timeout/failure fallback;
- better provenance wins close tie;
- recovery after first branch fails;
- agent cannot bypass T6;
- call budget;
- checkpoint/resume;
- no private chain-of-thought persisted.

PLAYWRIGHT
Show branch summaries, evidence IDs, scores, prune reasons, selected branch, deterministic PAP.

DOCUMENT
docs/lessons/11-agent-generation-critique-deterministic-control.md.

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
