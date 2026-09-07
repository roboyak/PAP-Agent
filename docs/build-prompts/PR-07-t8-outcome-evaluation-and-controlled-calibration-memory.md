# PR 07 — T8 Outcome Evaluation and Controlled Calibration Memory

```text
You are working on PR 07 of the DragonWings PAP Agentic Automation MVP v4.

BRANCH
feature/07-outcome-evaluation-memory

GOAL
Implement outcome evaluation and validated feedback across graph executions.

Lesson: **feedback becomes memory only after deterministic evaluation**.

ObservedOutcome
- PAP/interval id;
- actual generation;
- actual load;
- actual availability if computable;
- observed_at;
- provenance;
- validation status.

T8 OutcomeEvaluator
Compute only metrics supported by fixture data:
- absolute/relative error;
- calibration/coverage signal;
- source-specific error summaries;
- false/missed low-availability indicators when supported.

POSTGRESQL
Separate:
- raw outcomes;
- derived metrics;
- approved calibration summaries.
Preserve lineage.

CONTROLLED INFLUENCE
Validated calibration may influence future confidence calibration.
It cannot modify hard T5/T6 authority or site policy.

LANGGRAPH
Add evaluation node/flow after publication where an observed outcome exists or as a separate evaluation graph invoked later.
Keep graph behavior explicit and resumable.

SYNTHETIC DEMO
Repeated cloudy outcomes show baseline solar overestimation.
A later similar scenario receives lower confidence while deterministic physical math remains unchanged.

API/UI
- ingest synthetic outcome;
- inspect evaluation/calibration;
- show recent forecast-vs-outcome results.

TEST
invalid outcome rejected, deterministic metrics, validated-only calibration, hard constraints unchanged, graph persistence/resume, cloudy regression.

PLAYWRIGHT
forecast -> outcome -> later forecast -> visible calibration effect.

DOCUMENT
docs/lessons/07-feedback-with-guardrails.md.

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
