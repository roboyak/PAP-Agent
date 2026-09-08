# PAP quick start

```bash
make bootstrap  # first run: install, create PAP database, migrate, seed
make run        # http://127.0.0.1:8000
```

Ctrl-C stops the app. No Docker. `.env.example` lists optional settings.

## Run and read the result

1. Open **Forecast**, choose **MySolArk**, a **wing**, and **Latest scrape**, then **Run PAP**.
2. Read the first-hour **kW**, twelve-hour **kWh**, confidence and hourly chart.
3. Read the agent's guidance and source timestamp. Saved results can become stale.
4. Use **Inspect this run** to see the evidence behind that exact result.

kW is power; kWh is energy across time. Zero means no extra solar allocation.
The baseline uses synthetic weather, constant load and no battery discharge.
It checks the voltage floor and never commands equipment. Withheld means no
validated profile; inspect the reason before running again.

## Watch the simulator

1. Choose **MySolArk**, a **wing**, and **Aug 30–Sep 6, 2026**.
2. Pick a starting **Pacific** time and **1 hour / 15 min**, then **Start simulation**.
3. Watch the clock, progress and forecast update automatically. Each step estimates twelve
   hours; the selected increment advances the replay clock, not the forecast interval.
4. **Pause** finishes the current step. **Resume** continues. **Results → Inspect** opens
   any saved step; **Back to simulation** returns to the progressing run.

One wing runs at a time, through September 6 midnight (end excluded). The replay runs faster
than real time, with a one-second pause between steps. It continues across page changes;
after stopping/restarting the server, explicitly **Resume**. Use one `make run` process.
**Run once** evaluates only the selected starting snapshot. **Start new** begins another run.
The latest simulator is restored on the home page; keep its URL to revisit an older run.

Historical scrapes must be at most five minutes old at the replay time. Stale/missing data
is **withheld**, then the simulator advances. Results count forecasts and withheld steps;
overlapping forecasts are not summed into weekly energy. This is telemetry replay, not a
battery physics simulator or a forecast-accuracy score. Choose **Latest scrape** for now.

To regenerate a short silent walkthrough (app running, simulator paused, FFmpeg installed):

```bash
uv run python scripts/record_simulator_demo.py --wing 1.21 --step 60
```

It saves MP4/WebM, screenshots and run metadata under `output/recordings/`.

## Debug in Inspector

Start with **Trace** to find where the workflow stopped, then inspect that step:

| Tab | Look for |
| --- | --- |
| Context | Evidence, assumptions and actual model inputs |
| Memory | Retrieved records, scores and why they were selected |
| Tools | MCP inputs, results, source time and elapsed time |
| Subagent | Provider/model, role, output, tokens and failures |
| Trace | Workflow order, branches, pruning and stop reason |
| Health | **Check service** for current dependency readiness |

Expand **Inspect raw details** for the original records. The run URL preserves the
same episode across Inspector and **View forecast**. **Back to simulation** follows the
simulator's latest result. **Reset view** clears the view only.
On desktop, the main forecast fits one screen. Inspector keeps its six tabs visible
while details scroll; expand **Session activity** for prior actions.
**Evaluate latest reading** records feedback; **Index memory** makes eligible feedback
retrievable. Manual memory search does not change the selected run.
Inspector keeps the chosen wing/time. Replay uses generic guidance and disables outcome
feedback; live feedback stays with its wing.

For calibration, open **Memory → Current calibration maintenance → Check current calibration**.
It shows recent errors, threshold settings and whether review is due. The saved-run summary
stays fixed. Collect fresh outcomes and re-tune ENV settings when conditions change; restart
after changing them. [Maintenance procedure and CLI](docs/CALIBRATION_MAINTENANCE.md).
ECE is unavailable for qualitative confidence; the drift signal compares recent error means.

For a reproducible demo, load the sunny fixture in Inspector. **Compare agent off / on**
uses one snapshot for both modes. Provider switches require restarting the app:

```bash
AGENT_BACKEND=ollama AGENT_MODEL=gemma3:4b make run
ENABLE_INTERPRETATION_AGENT=true make run
```

OpenAI/Claude keys and model examples: [README](README.md#switch-the-model-provider).
Local checks: `make verify` (includes Playwright).
