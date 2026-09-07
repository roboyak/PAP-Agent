# DragonWings PAP Agent

A read-only capstone MVP, built in twelve small PRs. It reads DW 1.24's persisted
MySolArk scrape, calculates a twelve-hour solar-surplus profile, and exposes the evidence,
memory, tool calls and agent decisions behind it. No Docker or Gradio.

## Run

Requires Python 3.12, uv, native PostgreSQL with pgvector, and local Ollama.
This Mac already has Postgres.app, `gemma3:4b`, and `nomic-embed-text:latest`.

```bash
make bootstrap   # dependencies, Chromium, PAP database, migrations, seed and memory
make run         # loopback service, http://127.0.0.1:8000
```

Stop the service with Ctrl-C. `make db-down` stops the separate PAP PostgreSQL cluster
and preserves its data. `make run` starts it again. For a synthetic source:

```bash
PAP_PROFILE=macmini-replay make run
```

`.env` is optional; [.env.example](.env.example) lists defaults. Environment variables win.
`DATABASE_URL` points to PAP storage on port 55432. `SOURCE_DATABASE_DSN` points to the
existing MySolArk source database. The adapter opens a read-only source transaction.
Do not point PAP migrations at the source database.

## Use the console

**Run PAP** reads the latest source and runs the durable workflow. **Load sunny fixture**
and **Read MySolArk now** select/inspect a source; **Calculate PAP** runs the numerical core.
**Evaluate latest reading** compares a newer scrape with the forecast. The sunny fixture's
**Evaluate cloudy demo** creates clearly labeled synthetic feedback.

| Inspector | What it shows |
| --- | --- |
| Context | Actual agent inputs, call/message counts, evidence and calculation |
| Memory | pgvector candidates, scores, selection/rejection reasons and outcome feedback |
| Tools | Discovered read-only MCP schemas, arguments, results and elapsed time |
| Subagent | Generator, critic and interpretation inputs, schemas, outputs, usage and limits |
| Trace | Graph nodes, IDs, reasoning mode, branches, pruning, scores and stop reasons |
| Health | Database, migrations, vectors, checkpoint, source and model readiness |

The UI is built from plain HTML/CSS/JavaScript following the reference's conversation and
inspector layout. Reset view clears browser state; published records remain in PostgreSQL.
Stored profiles are historical evaluations. Run again for fresh evidence.

## Voltage and available power

The fixed live battery floor is **305.2 V**, the scanned minimum that the user maps to their
approximately 30% SOC reserve. The scanned maximum was **394.3 V**. Future lower readings
do not lower this configured floor. At/below the floor, additional power is withheld.
SOC is not a measured input, and no voltage-to-SOC curve is inferred.

The current profile uses measured PV/load power with **synthetic weather factors**, constant
demand, and **zero battery-discharge budget**. kW is power; kWh is power multiplied by hours.
Live equipment capability is unconfigured; future battery voltage is not predicted. This
is evaluation-only guidance. It never commands a battery, inverter, generator or load.
The sunny fixture has its own synthetic 48 V floor / 5 kW cap and 10.600 kWh baseline.

## Agents and comparison

Ordinary runs remain linear and need no model generation. Recorded solar overestimation
above the demo threshold of 0.25 kW triggers selective search over baseline/refresh/withhold
guidance. Local LangChain `create_agent` generator and critic roles receive bounded evidence
and no tools. Python prunes invalid branches and owns all numerical/voltage constraints.

```bash
ENABLE_INTERPRETATION_AGENT=true make run
```

The optional third interpretation role defaults to **false**. **Compare agent off / on**
runs both modes on one telemetry/weather snapshot, regardless of that default. It reports
role calls, elapsed time and whether calculated power stayed identical. Advice and publication
status can differ. One pair is a latency observation, not proof of better answer quality.
A real pair in [PR11](docs/pr/PR-11.md) took 53 seconds / four calls with two roles versus
70 seconds / six calls with three roles; calculations matched, but the latter withheld.

Search bounds: three children per parent, beam two, at most one refinement, final submission
at depth three, and eight total model attempts per episode including the optional role.
Each call has a 45-second / 768-output-token limit and no retry. Interrupted attempts count;
checkpoint resume reuses their stored records. Missing or malformed search output can withhold.

`make memory-index` embeds project guidance and up to 100 validated outcome records using
local nomic-embed-text (768 dimensions). Exact pgvector cosine retrieval selects up to five;
version, source, expiry, score and duplicate checks reduce model context to at most three.
Scores are ranking aids, not probabilities. Real and synthetic outcomes remain separate.

## Verify and inspect

```bash
make verify       # format/lint, migrations, integration checks, Chromium Playwright
make verify-mac   # same gate plus a command-line demo using explicit model doubles
make demo         # synthetic-source demo using configured local models
```

Tests own disposable `pap_test_*` databases and never alter the MySolArk source.
`test-results/` contains ignored browser screenshots. The CLI demo prints readiness,
PAP IDs, a stale-data rejection and paired results; it leaves no PAP/MCP child process.
It stores labeled synthetic records in PAP. Existing outcome feedback can make its first
run selective. The database remains available for inspection.

`/health/live` checks the service; `/health/ready` checks dependencies without persisting
probe evidence. `/health` retains the simple DB/vector check. `/docs` lists the API.
`GET /api/v1/pap/latest`, `/api/v1/episodes/{id}` and `/api/v1/episodes/{id}/inspection`
provide publication, workflow and local audit records.

Full prompts, tools and decisions stay local. `ENABLE_LANGSMITH=true` optionally exports
only an allowlisted run summary using locally configured LangSmith credentials. Automatic
SDK tracing stays disabled; export failure cannot change a PAP decision.

See the [runbook](docs/MVP_RUNBOOK.md), [final architecture](docs/architecture/FINAL_MVP.md),
[capstone review](docs/CAPSTONE_NOTES.md), and terse [PR lessons](docs/pr).
[The reference repository](https://github.com/jabarkle/Agent-with-Subagent) guided the agent
boundaries and inspector; PAP is its own repository and UI. Deep Agents is outside this MVP.
