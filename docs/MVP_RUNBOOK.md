# Local MVP runbook

Run commands from the repository root. Use a terminal; no Docker, daemon installation,
root privileges or hardware connection is needed.

## First setup

The supported path is Postgres.app with pgvector plus uv and Ollama. `PG_BIN` can override
`/Applications/Postgres.app/Contents/Versions/latest/bin`. Install the two local models if
this is a different Mac:

```bash
ollama pull gemma3:4b
ollama pull nomic-embed-text:latest
make bootstrap
make run
```

Bootstrap installs Python dependencies and Playwright Chromium, initializes a separate PAP
cluster under `.cache/postgres`, migrates, seeds the sunny fixture and indexes local memory.
It preserves existing data. The PAP role can create the disposable databases used by tests.
PostgreSQL binds to 127.0.0.1:55432; FastAPI binds to 127.0.0.1:8000. `PAP_PORT` overrides
only the service port. The bundled PAP password is for this local development cluster.

## Profiles and sources

| Profile | Default source | Models |
| --- | --- | --- |
| development | Latest persisted DW 1.24 MySolArk scrape | Configured provider; Ollama by default |
| macmini-replay | Sunny synthetic fixture | Configured provider; Ollama by default |
| test | Sunny fixture | Tests explicitly select deterministic doubles |

Set `PAP_PROFILE` before starting. The UI's source buttons can explicitly select another
source. Tests set `AGENT_BACKEND=test` and `EMBEDDING_BACKEND=test`; those results are labeled
test doubles, never real model measurements.

Set `AGENT_BACKEND` and `AGENT_MODEL` together to switch between local Ollama, OpenAI,
and Claude; see the [provider commands](../README.md#switch-the-model-provider). Cloud keys
are `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`, configured locally. Restart after changing them.
Embeddings still require Ollama. Cloud readiness checks configuration, not account access.

MySolArk is read from `pubnub_development` through `/tmp` by default. Configure its existing
connection using `SOURCE_DATABASE_DSN`, independently of PAP's `DATABASE_URL`. Source reads
use read-only transactions. Scrape timestamps are Rails UTC; they are not verified device
measurement times. Scrapes older than five minutes are rejected. No raw source JSON or
device identifiers are copied into PAP responses.

`BATTERY_FLOOR_V=305.2` is fixed from the user-approved observed minimum. It represents their
approximately 30% reserve convention; the service does not derive SOC or battery capacity.
Weather is synthetic, battery discharge is budgeted as zero, and live equipment cap is unknown.

## A short walkthrough

1. Open http://127.0.0.1:8000 and click Check service. Health should show readiness checks true.
2. Click Run PAP. Inspect source timestamp, floor, hourly kW/kWh and the six debug tabs.
3. Wait for a newer MySolArk scrape, then Evaluate latest reading. Memory shows point-power errors.
4. Index memory to include new outcomes. Compare agent off / on to inspect one paired run.
5. For a repeatable synthetic case, load sunny, run, evaluate cloudy, then run/compare again.

`ENABLE_INTERPRETATION_AGENT=false` is the default. Set it true before startup to add the
third interpretation role to normal Run PAP requests. Comparison explicitly tests both.
Generator/critic run only when recorded evidence triggers ambiguity. Their role count is
not their call count: one refinement may call the same role again.

## Verification and process lifecycle

```bash
make verify
make verify-mac
make demo
```

`make verify` runs deterministic model doubles with real local PostgreSQL/MCP/HTTP/Chromium.
`make verify-mac` adds the CLI demo with those doubles. `make demo` uses synthetic source
inputs and the configured model provider. All demo outcomes remain labeled synthetic.
The demo prints IDs and exits; inspect persistent records via API or the console.

`make run` is the foreground process strategy for this small CLI MVP. Ctrl-C stops FastAPI;
MCP subprocesses are scoped to each acquisition. `make db-down` stops only this PAP cluster.
No login agent is installed, so disabling means stopping these processes. Keep `.cache/postgres`
when removing/replacing code; it contains the local data. Logs go to the service terminal and
`.cache/postgres/server.log`; domain audits live in PAP tables. Screenshots are in `test-results/`.

If readiness is unavailable, inspect its named false check. Start PostgreSQL with `make db-up`,
apply migrations with `make migrate`, or start Ollama with the two configured models. Refresh
MySolArk scraping in DW if its source is stale. Liveness stays available while a dependency is down.

## Optional LangSmith

Set `ENABLE_LANGSMITH=true`, `LANGSMITH_API_KEY` and optionally `LANGSMITH_PROJECT` locally.
Only episode/publication IDs, status, reasoning mode, call count and profile/source labels are
exported after a completed API run. No prompts, raw telemetry, retrieved text or private reasoning
are exported. SDK automatic tracing remains explicitly disabled. Export has bounded timeouts,
no retries and a non-fatal failure path. This integration was tested with a fake client;
no remote export was performed during the build.
