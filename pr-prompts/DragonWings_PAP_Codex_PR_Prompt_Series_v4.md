# DragonWings PAP Agentic Automation MVP v4
## Sequential Codex PR Prompt Series — LangGraph / LangChain

### Runtime architecture

- LangGraph = core harness/state machine
- LangChain `create_agent` = selected probabilistic graph nodes
- PostgreSQL = relational system of record
- pgvector = semantic RAG memory
- LangGraph PostgreSQL checkpointer = durable execution state
- MCP = read-only Telemetry and Weather/Solar boundaries
- deterministic Python = T3/T4/T5/T6 + budgets/hard pruning/final authority
- LangSmith = optional tracing/evaluation
- Deep Agents = intentionally excluded from PAP MVP
- Playwright + pytest = required local verification
- only a human may push/open/approve/merge final PRs

### PR sequence

| PR | Increment | Lesson |
|---|---|---|
| 01 | Repo + PostgreSQL/pgvector + verification | Harness before intelligence |
| 02 | Typed domain + relational schema | Explicit state before orchestration |
| 03 | MCP sources + T3 | Integration is not trust |
| 04 | T4/T5/T6 deterministic core | Deterministic authority |
| 05 | LangGraph core harness | Graph owns control |
| 06 | T7 UI + observability | Make behavior inspectable |
| 07 | T8 outcomes/calibration | Validated feedback |
| 08 | T9 pgvector memory | Semantic external memory |
| 09 | RAG quality + first LangChain agent node | Bounded agent interpretation |
| 10 | Selective ToT subgraph | Structured search |
| 11 | LangChain generator/critic nodes | Probabilistic roles, deterministic control |
| 12 | Mac mini MVP runtime | Deploy safely and audibly |

### Fresh Codex session header

```text
This is an incremental PR in an existing repository.

Read AGENTS.md, docs/engineering/, relevant docs/lessons/, and the current implementation/tests before modifying code.

LangGraph is the core harness.
LangChain create_agent is used only inside selected graph nodes.
Deep Agents is not part of the PAP MVP.
PostgreSQL is the system of record.
pgvector is semantic memory.
Telemetry and weather enter through read-only MCP.
T3/T5/T6 deterministic authority cannot be bypassed.

Implement only the current PR scope.
Do not pull future milestones forward.
Never weaken validation or safety to make a test pass.
Run the complete local quality/HIL handoff workflow.
Do not push, open, approve, merge, or tag remotely.
```

---

# PR 01 — Repository, PostgreSQL/pgvector, and Verification Harness

```text
You are working on PR 01 of the DragonWings PAP Agentic Automation MVP v4.

BRANCH
feature/01-agentic-service-foundation

GOAL
Create the smallest runnable repository, PostgreSQL/pgvector persistence foundation, and local verification harness.

Lesson: **harness and durable infrastructure before intelligence**.

IMPLEMENT
1. Python src-layout package.
2. Minimal FastAPI service.
3. GET /health and GET /api/v1/version.
4. Typed settings with DATABASE_URL and safe local defaults.
5. PostgreSQL repository/session layer.
6. Alembic migrations; enable pgvector extension explicitly.
7. Real DB health query.
8. Reproducible local PostgreSQL+pgvector development path; pinned Compose/container is acceptable.
9. Minimal `/` page with DragonWings PAP Forecaster, READ ONLY, synthetic/local mode.
10. pyproject dependencies only for this increment.
11. pytest for health/version/config/database.
12. Playwright Python live-service smoke test.
13. Make targets: setup, db-up, db-down, migrate, dev, format, format-check, lint, test, e2e, verify.
14. .env.example and .gitignore.
15. Keep the existing quality/governance files intact.
16. docs/lessons/01-agentic-harness.md.

ARCHITECTURE
Do not add Deep Agents.
Do not add another vector database.
Application LangGraph/LangChain behavior is intentionally deferred.

ACCEPTANCE
- fresh setup documented;
- DB reachable;
- pgvector enabled;
- migrations from empty DB succeed;
- service loopback only;
- no required external cloud service;
- Playwright passes;
- make verify passes.

SPECIAL
Use `db-migration-safety`.

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

---

# PR 02 — PAP Domain Contracts, Relational Schema, and Synthetic Scenarios

```text
You are working on PR 02 of the DragonWings PAP Agentic Automation MVP v4.

BRANCH
feature/02-pap-domain-contracts

GOAL
Define typed domain state and relational persistence before orchestration.

Lesson: **typed state and auditable storage before agent behavior**.

Create typed models for:
- TelemetrySnapshot
- WeatherForecastInterval
- ReservePolicy
- ForecastInterval
- PowerAvailabilityInterval
- PAP
- AgentEpisodeRecord
- provenance/validation status structures

Use explicit units and timezone-aware timestamps.

POSTGRESQL
Create normalized migrations/tables/repositories.
Use JSONB only for bounded extensible metadata.
Add appropriate indexes/foreign keys.
Do not manually create LangGraph checkpointer tables; that arrives with PR05.

FIXTURES
Synthetic/public:
- normal sunny;
- rapidly changing cloud;
- low SOC;
- elevated wind;
- stale telemetry;
- missing field;
- contradictory sources.

Never imply fixture values are real DragonWings limits.

Fixture loading must be idempotent through repositories.

API
Development-only scenario list/detail endpoints.

TEST
- serialization/validation;
- invalid ranges;
- timezone behavior;
- repository round trips;
- migration from empty DB;
- idempotent fixtures;
- API contracts.

PLAYWRIGHT
Read a persisted fixture through the live API.

DOCUMENT
docs/lessons/02-explicit-domain-state.md.

NON-GOALS
No LangGraph graph, LangChain agent, RAG behavior, calculations, or real source integration.

SPECIAL
Use `db-migration-safety`.

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

---

# PR 03 — T1/T2 Read-Only MCP Sources and T3 Data-Quality Gate

```text
You are working on PR 03 of the DragonWings PAP Agentic Automation MVP v4.

BRANCH
feature/03-mcp-grounding-sources

GOAL
Implement grounded source acquisition through MCP.

Lesson: **MCP solves integration; T3 establishes trust**.

RULE
Do not invent real DragonWings CAN IDs, serial frames, registers, site limits, or provider credentials.

TELEMETRY MCP
Expose read-only tools/resources such as get_current_telemetry().
Fixture/replay implementation only.
Include source, source timestamp, schema/version, provenance, missing/error status.
No write/control tool.

WEATHER/SOLAR MCP
Expose read-only forecast acquisition using deterministic fixtures.
Keep future provider details behind the MCP boundary.

PAP CLIENT INTEGRATION
T1/T2 adapters call MCP and map responses into typed domain records.
Keep transport details out of domain logic.

POSTGRESQL
Persist sanitized source observations and provenance before/with validation.

T3
Validate freshness, required fields, ranges, units, impossible states represented by schema, source availability, and mixed-time/contradictory observations.

FAIL CLOSED
- unavailable != zero;
- never invent missing values;
- stale/invalid evidence cannot proceed as valid.

API
GET /api/v1/evidence/current?scenario=<name>

TEST
- normal;
- stale;
- missing;
- malformed;
- timeout/unavailable;
- schema mismatch;
- persistence/provenance;
- prove no write/control MCP tool exists.

PLAYWRIGHT
Run live local MCP servers plus PAP service and verify normal/stale/missing flows.

DOCUMENT
docs/lessons/03-mcp-ground-before-reasoning.md.

SPECIAL
Use `mcp-contract-safety`.

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

---

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

---

# PR 05 — LangGraph Core Harness, Durable State, and Bounded ReAct-Style Flow

```text
You are working on PR 05 of the DragonWings PAP Agentic Automation MVP v4.

BRANCH
feature/05-langgraph-core-harness

GOAL
Introduce LangGraph as the top-level PAP harness.

Lesson: **the graph is the control plane; agents are optional nodes inside it**.

Do not introduce a live LangChain agent yet. First prove state, routing, persistence, retries, and safe termination deterministically.

STATE
Create typed serializable PAPGraphState containing IDs/status only where practical:
- episode/thread id;
- goal;
- source/evidence record IDs;
- validation status;
- forecast/calculation/constraint IDs;
- retry counters;
- fallback;
- reasoning mode;
- stop reason/status.

Do not duplicate large canonical domain records into checkpoint state unnecessarily.

GRAPH
Create explicit nodes:
- acquire_telemetry
- acquire_weather
- validate_evidence
- forecast
- calculate_availability
- validate_candidate
- finalize_episode

Use conditional edges for:
- valid/invalid;
- retry/fallback/stop;
- pass/reject.

Express the prior ReAct-like observe/assess/act/observe/revise-or-validate loop as explicit graph control.

BUDGETS
- max steps;
- bounded source retries;
- duplicate refresh suppression;
- no T4/T5 before T3-valid evidence;
- hard stop on unrecoverable invalid state.

CHECKPOINTING
Use the official LangGraph PostgreSQL checkpointer.
Keep checkpoint data logically separate from domain records.
Use in-memory saver for unit tests where persistence is not under test.
Use PostgreSQL saver for integration/runtime durable-execution tests.
Use the checkpointer's supported setup/initialization path rather than hand-authoring internal tables.

IDEMPOTENCY
Persist/create operations must remain safe under resume/replay.

TRACE API
GET /api/v1/episodes/{episode_id}
Return node/action summaries, evidence/result IDs, retries, validation, and stop reason.
Never expose private chain-of-thought.

TEST
- happy path;
- stale/source failure;
- retry then success;
- retry exhausted;
- invalid candidate;
- checkpoint persists;
- resume does not duplicate records;
- no route skips T3/T6;
- all fixtures reach END.

PLAYWRIGHT
Verify live normal and failure graph traces.

DOCUMENT
docs/lessons/05-langgraph-harness.md.

SPECIAL
Use `langgraph-workflow-safety`; use `db-migration-safety` if persistence setup changes.

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

---

# PR 06 — T7 PAP Publisher, Operator Console, and Local Graph Observability

```text
You are working on PR 06 of the DragonWings PAP Agentic Automation MVP v4.

BRANCH
feature/06-pap-publisher-console

GOAL
Add structured publication, human-visible local operation, and local graph observability.

Lesson: **an agentic workflow is only trustworthy when outputs and control flow are inspectable**.

T7 PUBLISHER
Publish only:
- T6-validated PAP, or
- typed insufficient_data / insufficient_confidence outcome.

Canonical PAP JSON:
- profile id;
- generated_at;
- horizon;
- intervals;
- confidence;
- freshness;
- constraints;
- evidence/provenance;
- validation results;
- explanation;
- episode/thread id.

Persist PAP/interval/evidence links in PostgreSQL.

GRAPH
Add publish/finalize nodes to the LangGraph flow.
Ensure publishing is idempotent under checkpoint replay.

API
- POST /api/v1/pap/run?scenario=<name>
- GET /api/v1/pap/latest
- GET /api/v1/pap/{id}
- GET /api/v1/episodes/{id}

UI
Minimal operator console:
- READ ONLY;
- synthetic/replay mode;
- latest PAP;
- current freshness;
- interval table;
- confidence;
- constraints;
- provenance;
- graph node/stop summary;
- trace link.

LOCAL OBSERVABILITY
Structured logs correlate:
- PAP id;
- episode/thread id;
- graph node;
- MCP source IDs;
- validation/stop reason.

LANGSMITH
Optional only.
If added now, make it disabled by default/non-blocking and use official tracing integration.
The edge runtime must remain correct without it.

PLAYWRIGHT
- normal scenario renders PAP/provenance;
- stale scenario renders insufficient state;
- trace shows route/stop reason;
- no private chain-of-thought displayed;
- no fabricated power shown as valid.

TEST
Publisher refuses unvalidated candidates and remains idempotent on replay.

DOCUMENT
docs/lessons/06-structured-publication-observability.md.

SPECIAL
Use `langgraph-workflow-safety` and `observability-trace-safety`.

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

---

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

---

# PR 08 — T9 Semantic Retrieval with PostgreSQL + pgvector

```text
You are working on PR 08 of the DragonWings PAP Agentic Automation MVP v4.

BRANCH
feature/08-pgvector-semantic-retrieval

GOAL
Add semantic external memory using pgvector in the same PostgreSQL database.

Lesson: **stored knowledge becomes useful memory only when retrieval selects the right evidence**.

BOUNDARY
RAG is for:
- validated forecast/outcome episodes;
- synthetic operating guidance;
- public references.

RAG is not authoritative for:
- current MCP telemetry/weather;
- arithmetic;
- equipment limits;
- reserve enforcement.

EMBEDDING PROVIDER
- embed_documents;
- embed_query;
- deterministic test provider;
- configurable real development provider;
- automated tests never require network/model download;
- record model/version/dimension when real provider used.

PGVECTOR SCHEMA
Create semantic_memory_records with:
- record id/type;
- content;
- embedding vector;
- source/source id;
- date/validity;
- configuration class;
- event type;
- validation status;
- version;
- provenance;
- embedding model/version;
- timestamps.

For MVP scale, exact search is acceptable.
Only add HNSW/IVFFlat if model dimension is pinned and a benchmark justifies it.
Document similarity metric.

CORPUS
- structured forecast/outcome episode: one event per semantic record;
- narrative guidance/reference: semantic sections ~350–500 tokens with small overlap.

Only approved public/synthetic/anonymized validated records are embedded.

T9
Input natural-language retrieval need + metadata constraints.
Return first-stage FIVE candidates with score and provenance.

INGESTION
Idempotent CLI/job to select eligible records, chunk if needed, embed, version, and upsert.

Do not create Chroma/Pinecone/FAISS persistence.

TEST
migration, vector round trip, semantic retrieval with wording variation, metadata filters, validated-only indexing, idempotent reindex.

PLAYWRIGHT
Debug retrieval endpoint returns ranked IDs/scores/provenance.

DOCUMENT
docs/lessons/08-postgres-pgvector-memory.md.

SPECIAL
Use `db-migration-safety`.

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

---

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

---

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

---

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

---

# PR 12 — Mac mini Runtime Hardening, Optional LangSmith, and MVP Release Candidate

```text
You are working on PR 12 of the DragonWings PAP Agentic Automation MVP v4.

BRANCH
feature/12-mac-mini-runtime

GOAL
Turn the prototype into a safe local Mac mini MVP runtime.

Lesson: **production-quality agentic automation requires explicit process boundaries, readiness, durable state, budgets, observability, and safe failure**.

NO HARDWARE CONTROL.

RUNTIME PROFILES
- test
- development
- macmini-replay
No production-control profile.

POSTGRESQL/PGVECTOR
Document/automate one supported local Mac mini deployment path.
Readiness:
- reachable;
- migrations current;
- pgvector enabled;
- semantic query succeeds;
- writable.

LANGGRAPH
- PostgreSQL checkpointer initialized;
- graph compiles;
- readiness can create/read a safe checkpoint or equivalent supported health operation;
- max steps/retries/ToT budgets configured;
- resume behavior tested.

MCP
Run local read-only:
- Telemetry MCP;
- Weather/Solar MCP.

macmini-replay uses synthetic/replay implementations.
Readiness verifies schemas/versions and confirms no write/control tool exists.

PAP SERVICE
FastAPI/operator service on loopback.
T1/T2 call MCP.
T3-T8 deterministic/application nodes.
T9 PostgreSQL/pgvector.
LangChain agent nodes only where defined.
Selective ToT only when ambiguity trigger fires.

LOCAL PATHS
User-writable logs/replay/PAP exports.
No second vector database.

SERVICE LIFECYCLE
Provide:
- scripts/bootstrap_mac.sh
- scripts/run_local.sh
- scripts/verify_local.sh
- documented launchd templates/generator or an equivalent lightweight supervisor strategy
- disable/uninstall instructions.

Avoid root unless necessary.

HEALTH
- /health/live
- /health/ready

Ready requires:
- PostgreSQL/pgvector;
- graph/checkpointer;
- Telemetry MCP;
- Weather MCP;
- config;
- replay/source data;
- no forbidden control tools.

AUDIT
Structured local logs:
- PAP ID;
- episode/thread ID;
- graph node;
- agent node;
- MCP request/source ID;
- retrieval IDs;
- ToT branch/score/prune;
- validation;
- stop reason.

LANGSMITH
Optional development/evaluation integration.
Disabled/non-blocking by default on edge.
Trace failure never fails PAP.
No secrets/private chain-of-thought.

ONE-COMMAND LOCAL DEMO
- DB up/check;
- migrate;
- seed synthetic relational + semantic data;
- start MCP servers;
- start PAP service;
- normal scenario;
- stale scenario;
- RAG A/B;
- ToT ambiguity;
- print PAP IDs/statuses;
- clean stop.

UI
Banner:
READ-ONLY MVP — SYNTHETIC/REPLAY DATA

Show readiness and latest reasoning mode/PAP.

VERIFY
make verify includes:
- format/lint;
- migrations;
- unit;
- integration;
- MCP contract;
- pgvector;
- LangGraph transitions/checkpoint/resume;
- LangChain fake-agent tests;
- Playwright;
- startup readiness.

Add safe `make verify-mac`.

DOCS
- docs/MVP_RUNBOOK.md
- docs/architecture/FINAL_MVP.md
- docs/lessons/12-agentic-automation-baseline.md

FINAL_MVP must state:
- LangGraph harness;
- LangChain bounded agent nodes;
- PostgreSQL/pgvector;
- MCP boundaries;
- deterministic T3/T5/T6;
- selective ToT;
- optional LangSmith;
- Deep Agents excluded from MVP;
- all synthetic assumptions;
- requirements before real telemetry/weather integration.

REAL SOURCE NOTE
The capstone does not specify actual CAN IDs, framing, site limits, or final weather-provider credentials/contracts.
Keep source servers replay/fixture implementations and document sanitized contracts required for future integration.
Do not guess.

Suggest but DO NOT create/push:
v0.1.0-mvp

SPECIAL
Use every relevant specialized safety skill.

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
