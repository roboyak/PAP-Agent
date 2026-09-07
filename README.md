# DragonWings PAP Agent

Read-only power availability decision support, built one PR at a time.
**Current increment: PR06, published PAP and operator console.** Model nodes arrive later.

## Run locally

Requires Python 3.12, [uv](https://docs.astral.sh/uv/), and native PostgreSQL with pgvector.
This Mac's Postgres.app already provides PostgreSQL 17.4 and pgvector 0.8.0.
The default binaries are `/Applications/Postgres.app/Contents/Versions/latest/bin`;
set `PG_BIN` to use another installation. No Docker is needed.

```bash
make setup
make db-up
make migrate
make seed
make verify
make dev
```

Open <http://127.0.0.1:8000>. Stop the service with Ctrl-C; `make db-down` stops
PostgreSQL and preserves `.cache/postgres/`. `make db-up` initializes and starts this
project's native database on first use. Initial setup downloads Python packages and Chromium.
Runtime and verification need no cloud service or model.

`.env` is optional; [.env.example](.env.example) documents the local default. Environment
variables override it. `DATABASE_URL` is the PAP database, never the source telemetry database.
The bundled credentials are for synthetic local development. A separate PAP cluster binds to
`127.0.0.1:55432`; the service binds to `127.0.0.1:8000`.

| Route | Result |
| --- | --- |
| `/` | READ ONLY console with Context, Memory, Tools, Subagent, Trace, and Health tabs |
| `/health` | 200 when PostgreSQL responds and pgvector is enabled; otherwise 503 |
| `/api/v1/version` | Package version, read-only status, and local mode; no DB dependency |
| `/api/v1/scenarios` | Available local development fixtures |
| `/api/v1/scenarios/sunny` | Persisted voltage, solar/load power, weather intervals, and demo policy |
| `/api/v1/pap/latest` | Latest persisted publication, or null before the first run |
| `/api/v1/pap/{id}` | Canonical profile, provenance, constraints, and validation reason |
| `POST /api/v1/pap/run` | Run the durable workflow |
| `/api/v1/episodes/{id}` | Read the completed episode and node trace |
| `POST /api/v1/episodes/{id}/resume` | Resume or return a completed episode |
| `POST /api/v1/pap/calculate` | Acquire fresh evidence and persist the deterministic result |
| `/api/v1/calculations/{id}` | Read a stored calculation |
| `/api/v1/evidence/{id}` | Read the exact evidence used by a calculation |
| `/api/v1/evidence/current?scenario=mysolark` | MCP acquisition, T3 decision, persisted live evidence and calls |

Calculate PAP uses the last selected source (MySolArk by default). It produces a twelve-hour
solar-surplus profile, with a zero battery-discharge budget and explicit kW/kWh units.
The fixed `BATTERY_FLOOR_V=305.2` gates additional power at/below the floor; the user maps
that floor to their ~30% SOC reserve. Future lower readings cannot lower the configured floor.
The sunny fixture still uses its own synthetic 48 V / 5 kW policy. Live equipment capability
is unconfigured, and future voltage is not predicted. All results are an evaluation baseline.

Run PAP uses [LangGraph with its official PostgreSQL checkpointer](https://docs.langchain.com/oss/python/langgraph/add-memory).
Four nodes acquire validated evidence, calculate, publish, and finalize. Invalid evidence goes directly
to withheld publication. There are no automatic retries; the graph has an eight-step limit. The Trace
panel shows node results, IDs, and timing. PostgreSQL domain records remain canonical;
checkpoints hold IDs/statuses for resume. Cloud tracing is disabled. [PR06](docs/pr/PR-06.md)
includes inspection commands.

Run PAP fills the hourly availability table and restores the latest publication on reload.
Valid publications record evidence/calculation IDs, source timestamp, generation time,
voltage floor, confidence, and validation reason. Withheld publications retain their evidence
ID and rejection reason; profile/calculation/source fields may be absent. T7 rechecks freshness and constraints before
publication. Source age is shown when the page renders; a stored decision is historical, and
stale data requires a new run. Local logs correlate episode, PAP, evidence, node, and status.

## Code map

- `src/pap_agent/config.py`: typed local settings.
- `src/pap_agent/database.py`: connection pool and commit/rollback sessions.
- `src/pap_agent/main.py`: local page and API routes.
- `src/pap_agent/domain.py`, `store.py`, `seed.py`: typed records, explicit SQL, one sunny fixture.
- `src/pap_agent/static/`: plain HTML/CSS/JavaScript console; no Gradio or frontend build step.
- `migrations/`: pgvector and normalized telemetry, policy, scenario, and weather tables.
- `tests/`: configuration, API, real PostgreSQL, and live Playwright checks.

`make verify` checks formatting/lint, starts/migrates/seeds the DB, and runs all tests.
Tests create uniquely named `pap_test_*` databases and remove only those databases.
The test role needs database-creation privileges; the local setup creates a role with them.
`make test` runs API/config/DB checks; `make e2e` launches Uvicorn and Chromium itself,
checks every tab, keyboard/mobile layout, success and database failure, and saves
`test-results/pap-home.png` and `test-results/pap-mobile.png`.
Use `make format` to format code. Missing DB/browser dependencies fail verification.

The console follows the reference's conversation/inspector layout. Check service makes
real health/version requests and shows their status, timing, and JSON in Trace.
Reset view clears only the browser view. Context shows loaded evidence and Tools shows MCP
activity. Memory and Subagent have empty states until their capabilities are connected.
Load sunny fixture reads PostgreSQL and displays its evidence in Context. Fixture values
and the voltage-floor/power-cap policy are synthetic examples, not DragonWings ratings.
The fixture uses a fixed UTC replay clock. Repeated `make seed` preserves existing rows.

Read MySolArk now starts one local MCP process with two read-only tools, following the
reference's discover-tools/call-tool pattern using the [official MCP SDK](https://github.com/modelcontextprotocol/python-sdk).
Tools shows schemas, arguments, results, and timing. T3 checks required values and a five-minute
freshness limit. MySolArk is read directly from the local source database with its real scrape
timestamp (Rails UTC convention). The UI shows age in seconds. Scrape time is not verified device
measurement time. Weather remains synthetic. The live reserve floor is the user-approved 305.2 V observed minimum. `SOURCE_DATABASE_DSN` configures
the source; no device IDs, raw JSON, or credentials appear in evidence. Tests use an isolated
source-shaped database; normal MySolArk runs use the actual local source. See [PR03's notes](docs/pr/PR-03.md).

Migration `0001_enable_pgvector` leaves the shared vector extension installed on downgrade.
Downgrading `0002_domain_evidence` drops its four evidence tables; retain those tables
when rolling back an application version that has stored evidence.

## Build plan

The [PR prompts](docs/build-prompts/README.md) define the sequence. The
[capstone review](docs/CAPSTONE_NOTES.md) records the source comparison and accepted adjustments.
Lessons stay as one-line PR/commit notes in [docs/pr](docs/pr).

The planned architecture uses LangGraph for workflow control, PostgreSQL/pgvector for
storage and memory, read-only MCP sources, and deterministic calculations and validation.
LangChain agents are added only in their lessons. Deep Agents is outside this MVP;
LangSmith is optional. No hardware-control functionality is part of this project.
