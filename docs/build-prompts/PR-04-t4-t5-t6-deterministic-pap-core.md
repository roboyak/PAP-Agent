# PR 04 — T4/T5/T6 Deterministic PAP Core

```text
You are working on PR 04 of the DragonWings PAP Agentic Automation MVP v4.

BRANCH
feature/04-deterministic-pap-core

GOAL
Add the deterministic numerical and hard-validation core.

Lesson: **probabilistic reasoning never owns authoritative arithmetic or constraints**.

T4 Baseline PV/Demand Forecaster
- validated evidence in;
- typed ForecastInterval out;
- simple documented synthetic baseline;
- NON-PRODUCTION coefficients;
- uncertainty/model-version provenance.

T5 AvailabilityCalculator
- typed validated inputs only;
- keep kW vs kWh distinct;
- apply local demand + synthetic reserve;
- no LLM.

T6 ConstraintValidator
Hard-check:
- T3 validity/freshness;
- synthetic SOC floor;
- synthetic equipment limits;
- alarm blockers represented by fixtures;
- reserve policy;
- impossible negative/over-capacity outputs.

A T6 failure can never publish valid PAP.

Persist forecast/calculation/validation records in PostgreSQL.

API
POST /api/v1/pap/calculate

TEST
sunny, low SOC, high load, stale blocked, power/energy units, reserve effect, constraint rejection, deterministic repeatability.

PLAYWRIGHT
Same fixture twice -> identical numerical output.
Failure fixture -> never valid PAP.

DOCUMENT
docs/lessons/04-deterministic-tools.md.

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
