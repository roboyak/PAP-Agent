# Capstone source notes

Reviewed the 12-page `20260907_151637_UTC_Final_Capstone_Report_DragonWings_PAP_Section_B.pdf`,
the v4 PR prompts/quality pack, and [Agent-with-Subagent](https://github.com/jabarkle/Agent-with-Subagent).
Reference revision: `81ff9bec7e993ffa5f75c92ab44d49ce32e4e759`.
The starting directory contained planning materials, with no application implementation.

- Report: forecast 12-24 hours; account for battery energy across the whole horizon;
  validate before publishing; keep T1-T9 as services, with two LLM roles on ambiguous cases.
- Reference: borrow readable modules, narrow specialist tools, explicit context, and bounded
  loops. Per the user, build the UI from scratch in HTML/CSS/JavaScript, mimicking the
  sample's layout and Context, Memory, Tools, Subagent, and Trace tabs; add Health for
  local diagnostics. Do not depend on Gradio. Each panel should show the actual
  current context, eligible/selected memory, calls/results, isolated agent input/output,
  and concise execution events as those capabilities arrive. The PAP implementation
  follows the report's LangGraph and PostgreSQL architecture for orchestration/storage.
  The user explicitly permits adapting the reference's agentic Python as a baseline,
  incrementally; the UI remains our own implementation.
- The report's prior PR11 progress and example traces are reported history, not evidence
  that this new repository is implemented or benchmarked.
- PR01 builds only the service, database, and verification foundation. Keep one PR per lesson;
  lessons are terse PR/commit notes, per the user's preference.
- User authorized a new private PAP repo, pushes/PRs/merges after local Playwright passes,
  and autonomous progress after observing PR01/02. Build the smallest working vertical
  slice with minimal error handling; avoid exhaustive edge-case work. First connect
  MySolArk voltage/PV/load to a deterministic profile and the monitoring UI.
- Use native PostgreSQL command-line tools for the PAP database; no Docker dependency.
- Accepted PR09 adjustment: `ENABLE_INTERPRETATION_AGENT=false` by default. Enable the third,
  grounded interpretation agent for A/B performance comparison on identical evidence.
  Record quality, latency, and model-call counts; physical calculations retain authority.
  This flag is planned for PR09 and has no runtime behavior in PR01.
- PR10/11 must include the report's one-revision limit alongside branch factor 3, beam 2,
  depth 3, and eight total LLM calls, including retries and nested calls.
- Authorized future source: DW 1.24 **persisted MySolArk scrape data** in
  `/Users/roboyak/0_DragonWings/src/pubnub` and its local database (not CAN/Tesla records).
  PR02 uses synthetic evidence; PR03 adds read-only live source data and real timestamps. Battery voltage is the
  MVP battery-state input, per the user; SOC is not required. Keep voltage thresholds and
  any energy model explicit in configuration. Never infer equipment limits from measurements
  or copy source credentials into PAP.

## MySolArk source review (2026-09-07)

Source DB: local `pubnub_development`, PostgreSQL socket `/tmp/.s.PGSQL.5432`.
Read `telemetry_snapshots` with `message_type = 'solark_cloud'`; resolve DW 1.24 via
`sites.name` and require exactly one match. Keep the resulting device identifier inside
the read-only query. The review found 6,509 rows, with PV/load present in 6,359.

`solark_cloud_capture_service.rb` maps `solar_power_w`/`load_power_w` in watts and
`battery1_voltage` in volts. Timestamps are scrape time, not verified device measurement
time; make the source Rails UTC convention explicit. SOC fields are excluded from the MVP
by user decision. Battery power sign and capacity units still need validation if used later.

PR03 user update: use real data and real time to simplify evaluation. MySolArk is now read
directly from the source DB; retain the real scrape UTC timestamp and display its age.
No source data is modified. Keep device identifiers, raw JSON, and source credentials out
of PAP responses. Weather remains an explicit synthetic fixture for this increment.

PR04 policy direction: user explicitly asked to scan voltage history and assume its observed
minimum is the battery floor. The read-only scan of 6,527 MySolArk rows on 2026-09-07 found
305.2 V minimum and 394.3 V maximum. Treat this as a user-approved inferred floor, not a
manufacturer rating. The first calculation uses solar surplus only; no battery capacity or
SOC is inferred from voltage.

User clarified that the observed 305.2 V floor corresponds to their ~30% SOC reserve and
batteries must stay above it. Configure 305.2 V as a fixed hard floor; do not automatically
lower it from future minima. Continue calculations in voltage; do not derive an SOC curve.

## Completed MVP choices

PR01–12 implement the native CLI service, real read-only MySolArk adapter, deterministic
PAP, durable graph, observed outcomes, local pgvector memory, optional interpretation and
bounded generator/critic search. The final runbook documents foreground startup instead of
adding a daemon manager. At PR12, weather remained synthetic and battery energy was budgeted as zero.
The three-role comparison measures identical-evidence latency/call counts and exposes advice
for review; the observed real-model pair did not establish a quality improvement. The fixed
305.2 V floor and optional-third-role default remain unchanged. LangSmith is summary-only,
optional and disabled; no remote tracing was exercised during the build.

## PR25: stored Open-Meteo weather

Replace synthetic weather on new MySolArk runs with stored rows in the same read-only
source database. All five wings have Open-Meteo observations across the replay week.
Replay selects the nearest observation at/before each interval start within 90 minutes;
this uses historical actuals across the horizon, not an as-of forecast backtest. Live uses
12 complete, current UTC-hour capacity-factor rows (updated within 24 hours), otherwise
tries observations without reading future actuals. An incomplete weather horizon withholds
at T3. Never silently substitute the fixture. Sunny stays synthetic.

Retain the conservative 0..1 ratio: interval irradiance/reference irradiance for observations,
or interval CF/reference CF for stored forecasts; zero reference gives zero throughout.
This cannot amplify morning PV or recover sunrise from a zero reading. T5/T6, voltage
floors and any configured extra-power cap remain authoritative. No battery discharge is
allocated. Source/model timestamps stay visible; new weather variants use distinct scenario
keys. Forecast version `solar-persistence-stored-weather-v1` separates new calibration and
outcome retrieval from prior synthetic-weather feedback. Existing synthetic episodes, evidence, outcomes, submission snapshots and
`docs/data/WEEK_PLAYBACK.md` numbers are preserved. See [PR25](pr/PR-25.md).

## PR19: wing selection and snapshot replay

The user authorized all wings' live MySolArk data, the August 30–September 6 Sunday-to-Sunday
week, and 1-hour/15-minute stepping. The UI runs one selected snapshot at a time. The period
is midnight Pacific to midnight Pacific, end excluded; persisted timestamps remain UTC.
The five wings are DW 1.21–1.25. Fixed positive minima and source coverage are recorded in
`docs/data/wing-floors.json`; this extends the user's observed-minimum policy, without
automatically lowering any floor or inferring an SOC curve. The scan is retrospective.
Replay checks age at the selected time at T3/calculation/T7 and cannot update live feedback.
Live feedback is per wing; recorded runs retain their source, selection and actual save time.
Submission decks/videos remain labeled snapshots of their original runs, not new replay evals.

## PR20: automatic historical replay

The user asked for a simulator that starts and advances on its own. Start/Pause/Resume runs
one selected wing through the remaining recorded week in 15/60-minute steps. Each step uses
the existing durable PAP workflow and retains its own Inspector record. PostgreSQL stores
progress; browser navigation does not stop the runner. Restart leaves it paused for Resume.
The simple single-process runner adds no hardware control, physics model or accuracy claim.

## PR21: checkpoint 6.1 calibration maintenance

Grader feedback praised deterministic T5/T6 authority and warned that ECE/distribution-shift
alarms need continuing threshold re-tuning as conditions change. The MVP has qualitative
confidence, so ECE remains unavailable. PR21 replaces lifetime-average/hard-coded escalation
with recent outcome windows, configurable bias/error-drift thresholds, live-feedback expiry,
a review-due reminder and policy snapshots retained through resume/publication. A read-only
CLI previews candidate ENV settings. T5/T6 constraints remain authoritative. See
[maintenance](CALIBRATION_MAINTENANCE.md) for the operator procedure and metric limits.

## PR22: a recorded power story

User review found the noon-start, solar-surplus forecast confusing. A read-only audit of
all five MySolArk wings found morning generation on all 35 wing-days, with source gaps;
no UTC/Pacific timestamp rewrite was needed. Playback retains a full-week default with explicit start/end days and shows
actual solar, site use and leftover solar in Pacific time, with a separate Future estimate.
Night/load and missing-data states have plain explanations. The forecast remains the same
current-PV/synthetic-weather baseline and explicitly does not model sunrise or sunset.
A chart-day selector reviews completed days without rerunning them. The recorder and source
audit are reusable scripts.

The user requested adjustable speed and verification across all five wings. Fast/Normal/Slow
controls only the pause between completed steps (0/1/3 seconds); each existing PAP workflow
still runs. The real-week verification script checks every wing through 168 hourly steps,
including Pause/Reload/Resume, saved speed and earlier-day review.
