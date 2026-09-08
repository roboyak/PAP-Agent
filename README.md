# DragonWings PAP Agent

A read-only capstone MVP, developed in small teaching PRs. It reads DW 1.21–1.25's persisted
MySolArk scrapes, calculates a twelve-hour solar-surplus profile, and exposes the evidence,
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

## Use the app

[Quick start and debugging guide](howto.md).
**Forecast** (`/`) puts the result first: additional kW, twelve-hour kWh, the hourly chart,
source age and agent guidance. **Inspect this run** opens **Inspector** (`/inspector`)
with the same episode. **View forecast** returns to that fixed result;
**Back to simulation** follows the simulator's latest result when replay is running.

Choose a **wing** and **Latest scrape**, or **Aug 30–Sep 6, 2026** for recorded history.
The week runs from Sunday midnight to Sunday midnight, Pacific time, excluding the end.
Choose a starting time and **1 hour / 15 min**, then **Start simulation**. PAP advances
through the week automatically, showing each result and a progress counter. **Pause** finishes
the current step; **Resume** continues. **Results → Inspect** opens a fixed episode while the
simulation continues; **Back to simulation** returns to its latest result. **Run once** still
evaluates a single snapshot. Forecasts remain twelve hourly intervals. Scrapes must be at
most five minutes old relative to the selected time; stale/missing steps are withheld.

The simulator runs one selected wing in one foreground service process, with a one-second
visual pause between steps. PostgreSQL saves progress; refreshing or leaving the page does
not stop it. Server restarts leave it paused until Resume. Use a single `make run`, without
multiple Uvicorn workers. The home page restores the latest simulation; save its URL for
later review. Results count valid/withheld steps, not accuracy or cumulative weekly energy.
This is recorded-telemetry replay, not a physical battery simulation.

**Run PAP** reads the selected source and runs the durable workflow. **Load sunny fixture**
and **Read MySolArk now** select/inspect a source; **Calculate PAP** runs the numerical core.
**Evaluate latest reading** compares a newer scrape with the forecast. The sunny fixture's
**Evaluate cloudy demo** creates clearly labeled synthetic feedback.
Inspector reruns and comparisons retain the selected wing/time. Live feedback and memory
are separated by wing. Historical replay uses generic guidance only and cannot update live
feedback; this avoids using later outcomes as earlier knowledge. The recorded source still
has `data_mode=live` (real origin); `selection.replay_at` distinguishes its historical clock.

| Inspector | What it shows |
| --- | --- |
| Context | Actual agent inputs, call/message counts, evidence and calculation |
| Memory | pgvector candidates, scores, selection/rejection reasons and outcome feedback |
| Tools | Discovered read-only MCP schemas, arguments, results and elapsed time |
| Subagent | Generator, critic and interpretation inputs, schemas, outputs, usage and limits |
| Trace | Graph nodes, IDs, reasoning mode, branches, pruning, scores and stop reasons |
| Health | Database, migrations, vectors, checkpoint, source and model readiness |

**Memory → Current calibration maintenance** checks recent point-power errors, configurable
escalation thresholds and review dates. Runs with outcome feedback keep the policy and outcome IDs used for
its decision. [Calibration maintenance](docs/CALIBRATION_MAINTENANCE.md) explains the ENV knobs
and read-only candidate preview. Confidence stays qualitative; ECE is explicitly unavailable.

The UI uses plain HTML/CSS/JavaScript. Its sand palette, monospaced type and outlined
diagram blocks follow the [BRC Forecast design reference](https://brcforecast.corbett.vc/system).
Inspector retains the original six-tab monitoring structure. Reset view clears browser state; published records remain in PostgreSQL.
Stored profiles are historical evaluations. Run again for fresh evidence.

The selected-run link restores the same result, evidence, memory and model records after reload.
Each tab starts with a readable summary; **Inspect raw details** opens the underlying records.
Trace lists completed workflow nodes in execution order. Model records are grouped by role.
Source/calculation previews clear the selected workflow, and manual memory search has its own
results. Long actions show elapsed time and a pending request while conflicting actions are disabled.

## Voltage and available power

Each wing uses a fixed observed-minimum voltage floor. The user maps this to approximately
30% SOC reserve. [The read-only scan](docs/data/wing-floors.json) records the source ranges:

| Wing | Fixed floor | Observed maximum |
| --- | ---: | ---: |
| DW 1.21 | 313.2 V | 393.3 V |
| DW 1.22 | 310.3 V | 393.2 V |
| DW 1.23 | 319.0 V | 389.2 V |
| DW 1.24 | 305.2 V | 394.3 V |
| DW 1.25 | 309.8 V | 393.5 V |

`BATTERY_FLOOR_V` remains the DW 1.24 override; other fixed floors are in `selection.py`.
Future lower readings do not lower these floors. At/below the floor, additional power is withheld.
The scan includes data after the replay week, so replay uses retrospective policy calibration
and is not an unbiased historical accuracy benchmark. Real-time freshness uses wall-clock time.
SOC is not a measured input, and no voltage-to-SOC curve is inferred.

The current profile uses measured PV/load power with **synthetic weather factors**, constant
demand, and **zero battery-discharge budget**. kW is power; kWh is power multiplied by hours.
Live equipment capability is unconfigured; future battery voltage is not predicted. This
is evaluation-only guidance. It never commands a battery, inverter, generator or load.
The sunny fixture has its own synthetic 48 V floor / 5 kW cap and 10.600 kWh baseline.

## Agents and comparison

Ordinary runs remain linear and need no model generation. Recorded solar overestimation
above the demo threshold of 0.25 kW triggers selective search over baseline/refresh/withhold
guidance. LangChain `create_agent` generator and critic roles receive bounded evidence
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

### Switch the model provider

Set the API key in the ignored `.env` file or your shell, then choose both `AGENT_BACKEND`
and `AGENT_MODEL` before starting the service. Stop the previous service with Ctrl-C first.

```bash
AGENT_BACKEND=ollama AGENT_MODEL=gemma3:4b make run
AGENT_BACKEND=openai AGENT_MODEL=gpt-4.1-mini make run
AGENT_BACKEND=anthropic AGENT_MODEL=claude-haiku-4-5-20251001 make run
```

OpenAI uses `OPENAI_API_KEY`; Claude uses `ANTHROPIC_API_KEY`. Local Ollama stays the default.
Cloud models receive the same bounded evidence and retrieved context used by local agents.
Embeddings and PostgreSQL stay local. Every model record and off/on comparison identifies
the selected provider and model, with elapsed time and call counts. Individual model records
also include token usage when the provider returns it.
Cloud calls request native JSON output and apply the same local validation, zero-tool boundary,
45-second timeout, 768-output-token cap and zero retries.

Use **Load sunny fixture**, then **Compare agent off / on** for each provider. Avoid evaluating
or indexing new outcomes between trials so the stored guidance stays comparable. Each off/on
pair shares one evidence snapshot; separate provider runs are separate snapshots of the fixed
synthetic fixture. This is a manual comparison, not a controlled model-quality benchmark.
Inspect Context and Subagent for the results. Set `ENABLE_INTERPRETATION_AGENT=true` if you
want an ordinary Run PAP request to make a model call even without recorded ambiguity.

The example models support native structured output: [OpenAI model documentation](https://developers.openai.com/api/docs/models/gpt-4.1-mini)
and [Claude structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs).
Choose another supported model through `AGENT_MODEL`. Required tests use fake HTTP responses
through the real cloud SDKs; no live cloud comparison has been measured yet.
Readiness checks cloud key presence only; account access is checked on an actual call.

`make memory-index` embeds project guidance and up to 100 validated outcome records using
local nomic-embed-text (768 dimensions). Exact pgvector cosine retrieval selects up to five;
version, source, expiry, score and duplicate checks reduce model context to at most three.
Scores are ranking aids, not probabilities. Real and synthetic outcomes remain separate.

## Verify and inspect

```bash
make verify       # format/lint, migrations, integration checks, Chromium Playwright
make verify-mac   # same gate plus a command-line demo using explicit model doubles
make demo         # synthetic-source demo using the configured model provider
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

Full audit records stay in local PostgreSQL. Selecting a cloud model sends its bounded
prompt/context to that provider. `ENABLE_LANGSMITH=true` optionally exports
only an allowlisted run summary using locally configured LangSmith credentials. Automatic
SDK tracing stays disabled; export failure cannot change a PAP decision.

See the [runbook](docs/MVP_RUNBOOK.md), [final architecture](docs/architecture/FINAL_MVP.md),
[capstone review](docs/CAPSTONE_NOTES.md), and terse [PR lessons](docs/pr).
[The reference repository](https://github.com/jabarkle/Agent-with-Subagent) guided the agent
boundaries and inspector; PAP is its own repository and UI. Deep Agents is outside this MVP.

## Capstone submission artifacts

The [versioned artifacts](submission/artifacts/) include the final report, 10-slide
presentation, three-slide 90-second pitch, recording script, video-link document, and
faculty Q&A brief. The [submission builders](submission/README.md) regenerate them from
editable source content:

```bash
bash submission/build.sh
```

This uses the installed Codex artifact runtime, separately from PAP's application dependencies.
Each build writes a new directory under `output/capstone/`. Record and add the video links
before Canvas submission; repository visibility remains the owner's final step.

To recreate the short (2:30) and full (9:00) silent app recordings, see the
[recording instructions](submission/README.md#app-recordings). Narration cues are editable;
add your own audio and hosted links before submitting a presentation video.

The three-slide [output walkthrough](submission/artifacts/DragonWings_Output_Walkthrough.pptx)
and [fresh-run video](submission/artifacts/DragonWings_Output_Demo.mp4) show the redesigned
Forecast page and explain an actual MySolArk result. Recreate them with
`scripts/record_output_demo.py` and `submission/build_output.sh`; see
[the output recording instructions](submission/README.md#output-walkthrough).
