"""Read-only coverage and morning-solar audit for the selected Pacific replay week."""

import json
from datetime import UTC, datetime

import psycopg
from psycopg.rows import dict_row

from pap_agent.config import Settings
from pap_agent.selection import REPLAY_END, REPLAY_START, WING_FLOORS


def audit() -> dict:
    rows = []
    with psycopg.connect(
        Settings().source_database_dsn.get_secret_value(), row_factory=dict_row, connect_timeout=3
    ) as connection:
        connection.read_only = True
        connection.execute("SET LOCAL statement_timeout = 30000")
        for wing in WING_FLOORS:
            site = f"%{wing}%"
            count = connection.execute(
                "SELECT count(*) AS n FROM sites WHERE name ILIKE %s", (site,)
            ).fetchone()["n"]
            assert count == 1, f"Expected one site for DW {wing}"
            days = connection.execute(
                """WITH readings AS (
                    SELECT (timestamp AT TIME ZONE 'UTC') AT TIME ZONE 'America/Los_Angeles'
                        AS local_at, solar_power_w, load_power_w, raw_json->>'plant' AS plant
                    FROM telemetry_snapshots
                    WHERE message_type = 'solark_cloud'
                    AND device_id = (SELECT device_id FROM sites WHERE name ILIKE %s)
                    AND timestamp >= %s AND timestamp < %s
                ), gaps AS (
                    SELECT *, local_at - lag(local_at) OVER (ORDER BY local_at) AS gap
                    FROM readings
                )
                SELECT local_at::date AS day, count(*) AS samples,
                    count(DISTINCT date_trunc('hour', local_at)) AS hours_with_samples,
                    min(local_at)::time AS first_sample, max(local_at)::time AS last_sample,
                    (min(local_at) FILTER (WHERE solar_power_w > 100))::time AS first_over_100w,
                    (max(local_at) FILTER (WHERE solar_power_w > 100))::time AS last_over_100w,
                    count(*) FILTER (WHERE solar_power_w > 100 AND local_at::time < '12:00')
                        AS morning_solar_samples,
                    max(solar_power_w) FILTER (WHERE local_at::time < '12:00') / 1000.0
                        AS morning_peak_kw,
                    max(extract(epoch FROM gap)) / 60.0 AS largest_gap_minutes,
                    count(*) FILTER (WHERE plant NOT ILIKE %s) AS plant_label_mismatches,
                    count(*) FILTER (WHERE solar_power_w IS NULL OR load_power_w IS NULL)
                        AS missing_power_samples
                FROM gaps GROUP BY local_at::date ORDER BY day""",
                (site, REPLAY_START.replace(tzinfo=None), REPLAY_END.replace(tzinfo=None), site),
            ).fetchall()
            rows.extend({"wing": wing, **dict(day)} for day in days)
    return {
        "checked_at": datetime.now(UTC).isoformat(),
        "source": "DW telemetry_snapshots, message_type=solark_cloud; same site lookup as PAP",
        "solar_field": "solar_power_w, written from MySolArk flow.pvPower",
        "timezone": "America/Los_Angeles (PDT, UTC-07:00 for this week)",
        "start_inclusive": REPLAY_START.isoformat(),
        "end_exclusive": REPLAY_END.isoformat(),
        "threshold_w": 100,
        "note": "First reading above 100 W is not sunrise. Timestamps record scraper capture time.",
        "days": rows,
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, default=str))
