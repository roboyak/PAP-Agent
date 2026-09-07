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
  Inspect read-only and use anonymized replay samples for PR02/03. Battery voltage is the
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

For replay, select a bounded window under `BEGIN READ ONLY`; export only an anonymous
site alias, relative time, voltage, PV/load, and missing-data flags. Omit raw JSON,
source identifiers, locations, and original timestamps. Keep original scraped observations
distinct from synthetic happy-path fixtures and any explicit simulation assumptions.
No source data was exported or changed during this review.
