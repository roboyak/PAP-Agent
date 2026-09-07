# PR 10 — Selective Tree-of-Thought LangGraph Subgraph and Bounded Beam Search

```text
You are working on PR 10 of the DragonWings PAP Agentic Automation MVP v4.

BRANCH
feature/10-selective-tot-subgraph

GOAL
Add selective Tree-of-Thought as a bounded LangGraph subgraph.

Lesson: **structured search is an explicit graph mechanism, not a longer prompt**.

DEFAULT
Routine PAP remains linear.

AMBIGUITY ASSESSMENT
Use observable grounded flags such as:
- forecast-source disagreement;
- rapidly changing cloud;
- uncertain derating;
- multiple documented fallbacks;
- contradictory-but-usable retrieved evidence.

Use synthetic/configured thresholds, never invented production limits.

Invoke ToT only when multiple grounded interpretations remain plausible.

TREE CONTRACT

Thought:
candidate forecast strategy/operational hypothesis with evidence emphasized, uncertainty interpretation, fallback, and guidance implication.

Node/branch record:
- branch/node id;
- parent;
- depth;
- evidence IDs;
- thought summary;
- hard-check results;
- score;
- status;
- prune reason.

Persist tree metadata in application tables or domain-owned branch tables as appropriate; checkpoint state may reference IDs.

BOUNDS
- branch factor 3;
- beam width 2;
- max depth 3;
- max reasoning/model calls 8;
- early stop when one valid branch clearly dominates.

DEPTH INTENT
0 validated state + selected T9 evidence
1 three interpretations/source-weighting strategies
2 confidence/uncertainty/fallback/guidance refinement
3 candidate interpretation submitted to T5/T6

DO NOT BRANCH OVER
SOC arithmetic, reserve arithmetic, equipment limits, safety rules, T5 formula.

IMPLEMENTATION
Build deterministic application-owned beam/BFS control within a LangGraph subgraph.
For this PR use deterministic candidate/evaluator fixtures or interfaces so search mechanics are testable independently of live model quality.

PR11 will plug LangChain generator/critic nodes into these interfaces without changing beam-control authority.

TEST
- routine case skips ToT;
- ambiguous case enters;
- branch/beam/depth/call bounds;
- branch pruning;
- recovery when best-first branch fails;
- no acceptable branch -> lower confidence/abstain;
- checkpoint/resume does not duplicate branches;
- all paths terminate.

PLAYWRIGHT
Normal vs ambiguous trace shows `linear` vs `selective_tot`, branch summaries, prune reasons, final result — no private chain-of-thought.

DOCUMENT
docs/lessons/10-selective-tot-subgraph.md.

SPECIAL
Use `langgraph-workflow-safety`.

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
