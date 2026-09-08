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

For history, choose **Aug 30–Sep 6, 2026**, pick a **Pacific** time, then **1 hour / 15 min**
and the arrows to step through the week. **Run PAP** evaluates that one snapshot; the output
stays hourly. Sunday midnight September 6 is excluded. **Historical replay** is labeled and
uses the preceding scrape (maximum five minutes old). Change back to **Latest scrape** for now.

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
same episode across Forecast and Inspector. **Reset view** clears the view only.
On desktop, the main forecast fits one screen. Inspector keeps its six tabs visible
while details scroll; expand **Session activity** for prior actions.
**Evaluate latest reading** records feedback; **Index memory** makes eligible feedback
retrievable. Manual memory search does not change the selected run.
Inspector keeps the chosen wing/time. Replay uses generic guidance and disables outcome
feedback; live feedback stays with its wing.

For a reproducible demo, load the sunny fixture in Inspector. **Compare agent off / on**
uses one snapshot for both modes. Provider switches require restarting the app:

```bash
AGENT_BACKEND=ollama AGENT_MODEL=gemma3:4b make run
ENABLE_INTERPRETATION_AGENT=true make run
```

OpenAI/Claude keys and model examples: [README](README.md#switch-the-model-provider).
Local checks: `make verify` (includes Playwright).
