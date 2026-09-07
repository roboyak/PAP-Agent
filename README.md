# DragonWings PAP Agent

Read-only power availability decision support, built one PR at a time.
**Current increment: PR01, service and database foundation.** Forecasts and agents arrive later.

## Run locally

Requires Python 3.12, [uv](https://docs.astral.sh/uv/), and native PostgreSQL with pgvector.
This Mac's Postgres.app already provides PostgreSQL 17.4 and pgvector 0.8.0.
The default binaries are `/Applications/Postgres.app/Contents/Versions/latest/bin`;
set `PG_BIN` to use another installation. No Docker is needed.

```bash
make setup
make db-up
make migrate
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
| `/api/v1/version` | Package version, read-only status, and synthetic mode; no DB dependency |

## Code map

- `src/pap_agent/config.py`: typed local settings.
- `src/pap_agent/database.py`: connection pool and commit/rollback sessions.
- `src/pap_agent/main.py`: page and three HTTP routes.
- `src/pap_agent/static/`: plain HTML/CSS/JavaScript console; no Gradio or frontend build step.
- `migrations/`: Alembic enables pgvector; domain tables begin in PR02.
- `tests/`: configuration, API, real PostgreSQL, and live Playwright checks.

`make verify` checks formatting/lint, starts the DB, migrates it, and runs all tests.
Tests create uniquely named `pap_test_*` databases and remove only those databases.
The test role needs database-creation privileges; the local setup creates a role with them.
`make test` runs API/config/DB checks; `make e2e` launches Uvicorn and Chromium itself,
checks every tab, keyboard/mobile layout, success and database failure, and saves
`test-results/pap-home.png` and `test-results/pap-mobile.png`.
Use `make format` to format code. Missing DB/browser dependencies fail verification.

The console follows the reference's conversation/inspector layout. Check service makes
real health/version requests and shows their status, timing, and JSON in Trace.
Reset view clears only the browser view. Context, Memory, Tools, and Subagent have explicit
empty states until their capabilities are connected in later PRs.

Migration `0001_enable_pgvector` is additive. Downgrading to `base` deliberately leaves
the shared vector extension installed to protect data; upgrading again is supported.

## Build plan

The [PR prompts](docs/build-prompts/README.md) define the sequence. The
[capstone review](docs/CAPSTONE_NOTES.md) records the source comparison and accepted adjustments.
Lessons stay as one-line PR/commit notes. [PR01's draft](docs/pr/PR-01.md) has local review commands.

The planned architecture uses LangGraph for workflow control, PostgreSQL/pgvector for
storage and memory, read-only MCP sources, and deterministic calculations and validation.
LangChain agents are added only in their lessons. Deep Agents is outside this MVP;
LangSmith is optional. No hardware-control functionality is part of this project.
