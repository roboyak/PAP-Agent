# Final MVP architecture

LangGraph owns the durable workflow; PostgreSQL owns canonical facts. The official
PostgreSQL checkpointer stores references and control state. LangChain `create_agent`
exists only inside interpretation, generator and critic nodes. Deep Agents is excluded.

```mermaid
flowchart TD
  M[Read-only MCP: MySolArk + synthetic weather] --> Q[T3 validation]
  Q --> C[T4 forecast / T5 availability / T6 constraints]
  C --> A[Assess recorded ambiguity]
  A -->|routine| P[T7 recheck and publish]
  A -->|ambiguous or optional interpretation| R[T9 pgvector retrieval]
  R --> I[Optional interpretation + validator]
  R --> S[Selective LangGraph search]
  I -->|ambiguous| S
  I -->|routine| P
  S --> P
  P -->|Evaluate latest reading / cloudy demo| O[T8 observed outcomes and calibration]
  O -->|Index memory, then next retrieval| R
```

All source access is read-only. T1/T2 expose exactly two MCP tools. T3 validates typed
source envelopes, UTC scrape freshness and the twelve-hour weather horizon. Deterministic
Python owns T4 forecasting, T5 power/energy math, T6 voltage/cap checks and T7 publication.
It rechecks freshness and constraints after model work. No hardware-control tools exist.

The fixed live voltage floor is 305.2 V, mapped by the user to their approximate 30% reserve.
No dynamic minimum can lower it. The observed scan range was 305.2–394.3 V. Measured SOC,
battery capacity, discharge energy and a voltage/SOC curve are not inferred.

The minimal forecast uses current PV power times synthetic hourly factors and constant
measured load. Available kW is nonnegative solar surplus, capped only when a cap is configured;
kWh integrates each interval. Battery-discharge budget is zero. No future voltage guarantee
or real equipment-capability claim is made. Live equipment cap remains unconfigured.

T8 compares newer point-power samples with forecasts; it does not claim measured hourly energy.
Raw outcomes, metrics and source/version-specific confidence summaries are separate records.
A demonstration solar-overestimation threshold of 0.25 kW triggers ambiguity. T9 stores
768-dimensional local embeddings in pgvector, retrieves five, filters/version-checks and
selects at most three. Cosine scores and critic rubric scores are not probabilities.

Selective search has three children per parent, beam two, one refinement and depth-three
submission. Hard pruning precedes critique; Python selects the surviving guidance or withholds.
All roles together may reserve at most eight attempts. Every attempt is stored before its
bounded, zero-tool model call and reused on resume. The optional third interpretation role is
controlled by `ENABLE_INTERPRETATION_AGENT=false`; A/B reuses one canonical source snapshot.
Free-text advice can still be wrong. Structured fields/citations do not prove semantic truth.

The plain HTML/CSS/JS inspector exposes Context, Memory, Tools, Subagent, Trace and Health.
Audit records contain inputs, validated outputs, IDs, scores, prune reasons and limits,
never private chain-of-thought. Optional LangSmith receives only an allowlisted summary;
full local traces are independent of it. Its failure cannot change published decisions.

Native foreground scripts provide bootstrap/run/verify/demo. No Docker, secondary vector
store, daemon installation or production-control profile is included. Before operational
use, replace synthetic weather with a validated provider, establish actual equipment capability,
verify measurement-time semantics, and evaluate forecast/agent quality against held-out outcomes.
Real MySolArk integration is already present under the user's authorization; CAN formats,
provider credentials and site ratings were not invented.
