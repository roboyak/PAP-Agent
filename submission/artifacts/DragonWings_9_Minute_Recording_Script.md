# DragonWings PAP: slides and demos

Target: **9:10 total**, including slides, both demos and brief screen actions.
**1030 spoken words**; approximately 8.2 minutes at 125 words/minute before clicks and pauses. Rehearse once.

## Before recording

- Record each clip separately using the same screen dimensions and microphone. Leave about one second of silence at each end for trimming.
- Read only the narration. Actions are screen cues. Target times include brief clicks and pointing; rehearse once to check your pace.
- Use the existing ten-slide DragonWings_Final_Presentation deck. Slide 9 shows an earlier 44/13 test snapshot; its narration explicitly identifies the current 55/21 results.
- Before the PAP clip, have the local app running and other playback paused. Select MySolArk, DW 1.24, the recorded week, Start day Aug 30, End day Aug 30, 12:00 AM, 1 hour, Fast. This creates a short 24-step demonstration.
- Pre-open the saved real-data output in another tab: http://127.0.0.1:8000/?episode=976a617d-799f-464d-ae8f-224643488af2 . This saved example has 0.622 kW, 2.222 kWh, low confidence and five actual local model calls. Keep this same episode for Inspector.
- The repository remains private until its owner makes it public. Confirm reviewer access before submission. This script names the repository without claiming it is already public.
- Use the clip numbers below for playback order. Clip 09 is the PAP demo; slide 9 is clip 11. Trim times default to zero and can be adjusted after reviewing your recordings.

## Recording order

| Clip filename | Target | Finished-video position |
| --- | ---: | --- |
| 01-slide-01.mov | 0:20 | 0:00–0:20 |
| 02-slide-02.mov | 0:30 | 0:20–0:50 |
| 03-slide-03.mov | 0:40 | 0:50–1:30 |
| 04-slide-04.mov | 0:30 | 1:30–2:00 |
| 05-slide-05.mov | 0:30 | 2:00–2:30 |
| 06-slide-06.mov | 0:35 | 2:30–3:05 |
| 07-slide-07.mov | 0:40 | 3:05–3:45 |
| 08-slide-08.mov | 0:15 | 3:45–4:00 |
| 09-pap-demo.mov | 1:25 | 4:00–5:25 |
| 10-inspector-demo.mov | 2:20 | 5:25–7:45 |
| 11-slide-09.mov | 0:45 | 7:45–8:30 |
| 12-slide-10.mov | 0:40 | 8:30–9:10 |

## Slide 1: DragonWings Power Availability Profile Forecaster

**01-slide-01.mov · 0:20 · 0:00–0:20**

*Action: Show the title slide.*

My capstone is the DragonWings Power Availability Profile Forecaster, or PAP. It helps an operator understand how much extra solar power might be available, and inspect the evidence behind that estimate. I’ll explain the design, demonstrate PAP, and then show how we debug it.

## Slide 2: The operator’s planning question

**02-slide-02.mov · 0:30 · 0:20–0:50**

*Action: Point to the inputs, then the twelve-hour output.*

The operating question is simple: how much additional load might the next twelve hours support? A live reading tells us what is happening now, but planning needs an estimate of what comes next. PAP combines solar production, existing demand, and battery voltage. The output describes additional power and energy over twelve hours. The operator remains responsible for deciding whether to use it.

## Slide 3: One workflow connects the components

**03-slide-03.mov · 0:40 · 0:50–1:30**

*Action: Follow the architecture diagram from input to publication.*

LangGraph coordinates the workflow. Read-only tools acquire the telemetry and the demonstration weather inputs. Python checks freshness and units, calculates the profile, and applies the operating constraints. When the evidence calls for interpretation, the workflow retrieves relevant memory and invokes bounded model roles. A final check determines whether to publish or withhold the result. PostgreSQL stores the evidence and results, while checkpoints preserve workflow progress. This gives us an automatic process with a traceable decision at the end.

## Slide 4: Memory adds relevant experience

**04-slide-04.mov · 0:30 · 1:30–2:00**

*Action: Point to the retrieval and filtering stages.*

Memory gives the agent relevant experience from earlier work. We store operating guidance and qualified outcome comparisons, then search them using local vector embeddings. The system considers five candidates and keeps at most three after filtering. An operator can inspect which records were selected and why. This context can support a cautious explanation, but it cannot change the measured voltage or calculated power.

## Slide 5: Extra reasoning has a fixed budget

**05-slide-05.mov · 0:30 · 2:00–2:30**

*Action: Point to the routine path, then the bounded search branch.*

Routine cases take the direct path and need no model generation. When recorded errors justify more caution, a generator proposes a few interpretations and a critic evaluates the survivors. Python removes invalid candidates. The search allows one refinement and at most eight shared model attempts. These limits keep difficult cases bounded. The model may recommend refreshing evidence or withholding guidance, but it cannot rewrite the power formula.

## Slide 6: The third role added cost in one trial

**06-slide-06.mov · 0:35 · 2:30–3:05**

*Action: Point to the two comparison rows.*

An environment setting enables an optional third interpretation role. In one comparison using the same source snapshot, two roles took four calls and about fifty-three seconds. Three roles took six calls and about seventy seconds. The calculated power and energy stayed identical, while the publication outcomes differed. One comparison cannot establish better quality, so the third role defaults off. We can also switch between local Ollama, OpenAI, and Claude for further evaluation.

## Slide 7: Validation controls publication

**07-slide-07.mov · 0:40 · 3:05–3:45**

*Action: Point to the voltage floor and publish/withhold outcomes.*

The deterministic checks remain authoritative. For Wing one point twenty-four, the fixed observed voltage floor is three hundred five point two volts. The model cannot lower that floor, and PAP never commands equipment. Checkpoint feedback also highlighted calibration maintenance. We now monitor recent forecast errors, compare error windows when enough samples exist, and remind the operator to review escalation thresholds. Those thresholds still need human review as conditions change. They cannot override the voltage and calculation checks.

## Slide 8: Six views explain each decision

**08-slide-08.mov · 0:15 · 3:45–4:00**

*Action: Show the six-tab overview. Finish before switching to the browser.*

The six Inspector views make the system understandable when a result looks surprising. First, I’ll show the operator’s view of PAP. Then I’ll open one saved result and follow its evidence through Inspector.

## Demo 1: PAP playback and one forecast

**09-pap-demo.mov · 1:25 · 4:00–5:25**

*Action: Show the prepared DW 1.24 one-day controls with Fast selected. Start playback after this opening paragraph.*

This is PAP using real MySolArk recordings from our DragonWings units. I’ve selected Wing one point twenty-four and August thirtieth. Fast removes the added pause, while every calculation still runs. All display times are Pacific.

*Action: Start simulation now, then point to the solar, usage and leftover lines as the day advances. Allow the 24 steps to finish.*

Gold shows solar generation, the dashed line shows site usage, and green shows solar left over before battery charging or other limits. Morning production appears when the recorded readings show it. Overnight, solar falls away while usage continues. Missing readings appear as gaps. We can also select a full week and review completed days.

*Action: Switch to the prepared saved-output tab. Keep Future estimate selected.*

Now I’m opening a separate saved forecast from real telemetry. It estimates zero point six two two kilowatts of additional power in the first hour, and two point two two two kilowatt-hours over twelve hours. Confidence is low. This future estimate uses demonstration weather and does not predict sunrise or sunset. Let’s inspect exactly how this result was produced.

## Demo 2: Inspector for the same saved forecast

**10-inspector-demo.mov · 2:20 · 5:25–7:45**

*Action: Click Inspect this run on the saved 0.622 kW forecast, then select Context.*

Inspector is linked to the same saved result. Context shows the actual inputs and calculated facts supplied to its model roles. If an explanation seems wrong, this is where I check whether the agent received the right evidence.

*Action: Select Memory. Show the selected records and their reasons. Briefly point out Current calibration maintenance.*

Memory shows the guidance and earlier outcome records selected for this run, including relevance scores and selection reasons. Those scores rank relevance. They are not probabilities. The current calibration section is separate from this saved context. It helps the operator review recent errors, sample counts, and whether escalation thresholds need attention.

*Action: Select Tools and point to the source-call summaries.*

Tools shows the data calls, their status, and elapsed time. We can expand the inputs and returned evidence. Both source tools are read-only, and their results still pass validation before calculation.

*Action: Select Subagent. Show a generator or critic record with its provider and validated output.*

Subagent shows which roles actually ran, their model, duration, and returned output. This saved example used five local model calls. We can inspect the generator’s proposals and the critic’s evaluations. An ordinary replay step may correctly show no model calls because its evidence did not require extra reasoning.

*Action: Select Trace. Point to the ordered nodes, branch decision and stop reason.*

Trace connects the steps in order. It shows why the workflow took the selective path, which branches survived, and why the search stopped. These records make the decision process reviewable without exposing private model reasoning.

*Action: Select Health and click Check service. Point to current status without promising it will be green.*

Finally, Health checks the service now, including its database and model configuration. That current readiness is separate from the historical result. Together, these views let a human investigate the evidence behind an output.

## Slide 9: Evidence supports the integrated workflow

**11-slide-09.mov · 0:45 · 7:45–8:30**

*Action: Return to slide 9. Its on-slide 44/13 counts are the earlier snapshot; read the update below.*

This slide captures an earlier test snapshot. The latest suite now passes fifty-five backend tests and twenty-one browser tests. We also replayed all five wings across seven days: eight hundred forty hourly steps, with pause, reload, and resume verified for each wing. Eight hundred four steps published valid forecasts, and thirty-six were withheld without stopping playback. These results demonstrate completion and tested boundaries. The point errors shown here come from one later sample. Forecast accuracy still needs a larger, independent evaluation.

## Slide 10: Repository and next steps

**12-slide-10.mov · 0:40 · 8:30–9:10**

*Action: Show the repository address and next steps. Pause briefly after the final sentence.*

The repository is on GitHub at roboyak slash PAP-Agent. It includes setup instructions, the working code, tests, teaching notes, and scripts that regenerate the submission materials. The next priorities are validated weather, equipment limits, and repeated comparisons using held-out outcomes. The main accomplishment is an integrated system that produces an estimate, applies explicit limits, and preserves enough evidence for a person to understand and challenge the result. Thank you.

## Join the recordings

Put the twelve numbered MOV or MP4 files in one folder. Give the folder path to Codex for trimming and assembly, or use:

```bash
uv run python scripts/assemble_presentation.py --clips /path/to/your/clips
```

The command creates a new MP4 and timing receipt under output/recordings/. Original clips stay unchanged. Review the full result for audible narration, readable screens, clean cuts and an 8–10-minute duration before hosting it.

Edit submission/narration.json and run `uv run python submission/build_narration.py` to regenerate this reading copy. Per-clip trim_start/trim_end are seconds removed from the beginning/end, only when deliberately configured after review.
