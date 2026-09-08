# Five-wing playback verification

Automated local Chromium verification on September 7, 2026 (Pacific), using real persisted
MySolArk scrapes. Each wing replayed August 30 through September 5, midnight to midnight,
at one-hour increments on **Fast**. All **840 steps** completed.

| Wing | Steps | Valid forecasts | Withheld | Check duration |
| --- | ---: | ---: | ---: | ---: |
| DW 1.21 | 168 | 160 | 8 | 132.6 s |
| DW 1.22 | 168 | 158 | 10 | 146.8 s |
| DW 1.23 | 168 | 162 | 6 | 116.8 s |
| DW 1.24 | 168 | 162 | 6 | 114.3 s |
| DW 1.25 | 168 | 162 | 6 | 126.4 s |
| Total | 840 | 804 | 36 | |

Every run passed Pause → Reload → Resume, preserved Fast speed, had 24 unique steps per
Pacific day and 168 unique episodes, and offered all seven completed dates in Chart day.
The first-day review and Follow playback displayed the matching saved episode. The main
view fit 1366×768; no JavaScript errors occurred. Withheld steps did not stop playback.
The final receipt's actual wing identifiers were checked against DW 1.21–1.25.

Durations include browser checks, pause/reload and rendering; the first runs overlapped the
automated test suite. These are completion measurements, not controlled speed benchmarks.
Valid/withheld counts describe publication decisions, not forecast accuracy.

- [Machine-readable receipt and local run links](week-playback-verification.json)
- [Current UI with Fast selected](../../submission/examples/recorded-week/fast-playback.png)
- [Source coverage and morning-generation audit](MYSOLARK_WEEK.md)
- [Normal-speed DW 1.24 recording receipt](../../submission/artifacts/Recorded_Week_Verification.json)

With `make run` serving the app and playback idle, repeat with:

```bash
uv run python scripts/verify_week_playback.py
```

The script creates new PAP simulation/publication records, saves a new receipt, and writes
screenshots under `test-results/real-week-playback/`. Source telemetry stays read-only.
Fast removes the added inter-step pause; it still runs every PAP calculation.
