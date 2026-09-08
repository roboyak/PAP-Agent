# MySolArk recorded-week audit

The same site lookup and `solark_cloud` source used by PAP contains **24,113 scrapes** for
DW 1.21–1.25 across August 30–September 5, 2026 (Sunday-to-Sunday, end excluded).
All 35 wing-days have morning solar. Scraper `flow.pvPower` becomes `solar_power_w`;
site mappings agree with stored plant labels. No raw power fields are missing in this scan.

First recorded solar **above 100 W**, Pacific daylight time (UTC−7):

| Day | DW 1.21 | DW 1.22 | DW 1.23 | DW 1.24 | DW 1.25 |
| --- | --- | --- | --- | --- | --- |
| 2026-08-30 | 06:06 | 06:38 | 06:40 | 06:06 | 06:04 |
| 2026-08-31 | 06:06 | 06:48 | 06:34 | 06:06 | 06:04 |
| 2026-09-01 | 07:04 | 07:04 | 06:10 | 06:10 | 06:10 |
| 2026-09-02 | 06:42 | 07:06 | 07:00 | 06:36 | 07:02 |
| 2026-09-03 | 06:36 | 07:14 | 06:20 | 06:36 | 06:18 |
| 2026-09-04 | 06:56 | 09:14 | 07:16 | 06:56 | 06:54 |
| 2026-09-05 | 06:06 | 06:44 | 06:06 | 06:06 | 06:10 |

Times are the first observed threshold crossing, **not astronomical sunrise**. Every time
above is AM. Capture timestamps record when the scraper ran, not independently verified
inverter measurement times. The Rails timestamp is stored as naive UTC; PAP interprets it
explicitly as UTC and the viewer displays America/Los_Angeles. No timestamp shift was needed.

Coverage is not uninterrupted: seven wing-days contain gaps longer than an hour, mainly
September 2–3. DW 1.22 on September 4 first exceeds 100 W at 9:14 AM despite samples in
every hour; the record alone does not establish why. DW 1.23 on August 30 peaks at only
0.21 kW before noon. Neither exception justifies inventing or shifting generation.

[Machine-readable detail](mysolark-week-coverage.json) includes per-day counts, hourly coverage,
last generation time, morning peak and largest gap. The UI samples the latest eligible
scrape at each 15/60-minute step; it does not plot every two-minute raw scrape.

Regenerate from the repository root (read-only; source DB configured):

```bash
uv run --locked python scripts/audit_mysolark_week.py > docs/data/mysolark-week-coverage.json
```
