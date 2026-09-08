"""Read stored MySolArk telemetry and Open-Meteo weather, without HTTP or source writes.

For observations, x is shortwave radiation (W/m²); for hourly forecasts, x is
capacity factor. solar_factor = min(1, x_interval / x_reference), where reference
is the first selected row. A zero reference gives zero factors throughout: this
conservative persistence model cannot predict a sunrise from a zero solar reading.
The 0..1 contract stays unchanged, so morning ramps never amplify measured PV.
Cloud effects are already in irradiance; cloud cover is not multiplied in again.
T5/T6 and ReservePolicy remain authoritative over published additional power.

Replay selects the nearest observation at/before each interval start, at most
90 minutes old. This uses historical actuals across the horizon, NOT an as-of
forecast backtest. Live selects all 12 containing UTC-hour forecast buckets,
each updated at/before the horizon start within 24 hours, or retries the entire
horizon with observations available at the horizon start. No source mixing or
synthetic fallback: any missing/stale interval makes the result unavailable.
Intervals start at the telemetry time (no interpolation). source_time is that
horizon anchor; data.input_times/updated_times retain actual stored row times.
Rails timestamp-without-time-zone columns are explicitly interpreted as UTC.
"""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from math import isfinite
from typing import Literal
from uuid import NAMESPACE_URL, uuid5

import psycopg
from psycopg.rows import dict_row
from pydantic import AwareDatetime, BaseModel, Field

from pap_agent.config import Settings
from pap_agent.domain import WeatherForecastInterval
from pap_agent.seed import sunny_fixture
from pap_agent.selection import RunSelection


class SourceResult(BaseModel):
    schema_version: Literal["1"] = "1"
    status: Literal["ok", "unavailable"] = "ok"
    source: str
    source_time: AwareDatetime
    clock: Literal["replay", "wall"] = "wall"
    data: dict = Field(default_factory=dict)
    reason: str = ""


def telemetry_source(
    scenario: Literal["sunny", "mysolark"], selection: RunSelection | None = None
) -> SourceResult:
    selection = selection or RunSelection()
    if scenario == "sunny":
        snapshot = sunny_fixture().telemetry
        return SourceResult(
            source=snapshot.source,
            source_time=snapshot.observed_at,
            clock="replay",
            data=snapshot.model_dump(mode="json"),
        )
    source = f"DW {selection.wing} MySolArk persisted scrape"
    site = f"%{selection.wing}%"
    cutoff = (
        selection.replay_at.astimezone(UTC).replace(tzinfo=None) if selection.replay_at else None
    )
    try:
        with psycopg.connect(
            Settings().source_database_dsn.get_secret_value(),
            row_factory=dict_row,
            connect_timeout=3,
        ) as connection:
            connection.read_only = True
            connection.execute("SET LOCAL statement_timeout = 3000")
            count = connection.execute(
                "SELECT count(*) AS n FROM sites WHERE name ILIKE %s", (site,)
            ).fetchone()["n"]
            if count != 1:
                raise ValueError("Expected one source site")
            row = connection.execute(
                """
                SELECT timestamp AT TIME ZONE 'UTC' AS observed_at,
                       battery1_voltage AS battery_voltage_v,
                       solar_power_w / 1000.0 AS solar_power_kw,
                       load_power_w / 1000.0 AS load_power_kw
                FROM telemetry_snapshots
                WHERE message_type = 'solark_cloud'
                  AND device_id = (SELECT device_id FROM sites WHERE name ILIKE %s)
                  AND (%s::timestamp IS NULL OR timestamp <= %s)
                ORDER BY timestamp DESC LIMIT 1
            """,
                (site, cutoff, cutoff),
            ).fetchone()
        if row is None or any(value is None for value in row.values()):
            raise ValueError("Required scrape fields missing")
        observed_at = row.pop("observed_at").astimezone(UTC)
        # Keep existing DW 1.24 snapshot/outcome identities stable across this upgrade.
        identity = "pap:mysolark:" + ("" if selection.wing == "1.24" else f"{selection.wing}:")
        return SourceResult(
            source=source,
            source_time=observed_at,
            clock="replay" if selection.replay_at else "wall",
            data={
                "id": str(uuid5(NAMESPACE_URL, identity + observed_at.isoformat())),
                "observed_at": observed_at.isoformat(),
                **row,
                "source": source,
                "data_mode": "live",
                "measurement_time_verified": False,
            },
        )
    except (psycopg.Error, ValueError):
        return SourceResult(
            status="unavailable",
            source=source,
            source_time=datetime.now(UTC),
            reason="Source DB unavailable or required scrape fields missing",
        )


OBSERVATIONS = "Open-Meteo stored observations"
STORED_FORECAST = "Open-Meteo stored forecast"
OBSERVATION_TOLERANCE = timedelta(minutes=90)
FORECAST_MAX_AGE = timedelta(hours=24)


def solar_factor(value: float, reference: float) -> float:
    """Conservative irradiance/CF ratio; missing, negative or nonfinite is not zero."""
    if any(item is None or not isfinite(item) or item < 0 for item in (value, reference)):
        raise ValueError("Weather requires finite, nonnegative irradiance or capacity factor")
    return min(1.0, value / reference) if reference else 0.0


def _weather_rows(selection: RunSelection, starts_at: datetime) -> dict[str, list[dict]]:
    site = f"%{selection.wing}%"
    start = starts_at.astimezone(UTC).replace(tzinfo=None)
    end = start + timedelta(hours=11) if selection.replay_at else start
    hour = start.replace(minute=0, second=0, microsecond=0)
    with psycopg.connect(
        Settings().source_database_dsn.get_secret_value(),
        row_factory=dict_row,
        connect_timeout=3,
    ) as connection:
        connection.read_only = True
        connection.execute("SET LOCAL statement_timeout = 3000")
        if (
            connection.execute(
                "SELECT count(*) AS n FROM sites WHERE name ILIKE %s", (site,)
            ).fetchone()["n"]
            != 1
        ):
            raise ValueError("Expected one source site")
        observations = connection.execute(
            """SELECT observed_at AT TIME ZONE 'UTC' AS at,
                      shortwave_radiation_wm2 AS value
               FROM weather_observations
               WHERE device_id = (SELECT device_id FROM sites WHERE name ILIKE %s)
                 AND source = 'open-meteo' AND observed_at BETWEEN %s AND %s
               ORDER BY observed_at""",
            (site, start - OBSERVATION_TOLERANCE, end),
        ).fetchall()
        forecasts = []
        if not selection.replay_at:
            forecasts = connection.execute(
                """SELECT hour_utc AT TIME ZONE 'UTC' AS at, cf AS value,
                          updated_at AT TIME ZONE 'UTC' AS updated_at, model_version
                   FROM solar_forecast_hours
                   WHERE device_id = (SELECT device_id FROM sites WHERE name ILIKE %s)
                     AND hour_utc BETWEEN %s AND %s ORDER BY hour_utc""",
                (site, hour, hour + timedelta(hours=11)),
            ).fetchall()
    return {"observations": observations, "forecasts": forecasts}


def _observation_hours(rows: list[dict], times: list[datetime], replay: bool) -> list[dict]:
    selected = []
    for at in times:
        candidates = [row for row in rows if row["at"] <= (at if replay else times[0])]
        row = max(candidates, key=lambda row: row["at"]) if candidates else None
        if row is None or at - row["at"] > OBSERVATION_TOLERANCE:
            raise ValueError(f"No observation within 90 minutes before {at.isoformat()}")
        selected.append(row)
    return selected


def _forecast_hours(rows: list[dict], times: list[datetime]) -> list[dict] | None:
    by_hour = {row["at"]: row for row in rows}
    selected = []
    for at in times:
        row = by_hour.get(at.replace(minute=0, second=0, microsecond=0))
        if (
            row is None
            or row.get("updated_at") is None
            or not timedelta(0) <= times[0] - row["updated_at"] <= FORECAST_MAX_AGE
            or row["value"] is None
            or not 0 <= row["value"] <= 1
            or not row.get("model_version")
        ):
            return None
        selected.append(row)
    return selected


def _synthetic_weather(starts_at: datetime) -> SourceResult:
    intervals = sunny_fixture().weather
    origin = intervals[0].starts_at
    for item in intervals:
        offset = item.starts_at - origin
        item.starts_at = starts_at + offset
        item.ends_at = item.starts_at + timedelta(hours=1)
    return SourceResult(
        source="synthetic weather",
        source_time=starts_at,
        clock="replay",
        data={"intervals": [item.model_dump(mode="json") for item in intervals]},
    )


def weather_source(
    selection: RunSelection,
    starts_at: AwareDatetime,
    *,
    scenario: Literal["sunny", "mysolark"] = "mysolark",
    fetch_rows: Callable = _weather_rows,
) -> SourceResult:
    if scenario == "sunny":
        return _synthetic_weather(starts_at)
    starts_at = starts_at.astimezone(UTC)
    times = [starts_at + timedelta(hours=hour) for hour in range(12)]
    source = OBSERVATIONS if selection.replay_at else STORED_FORECAST
    fallback = ""
    try:
        rows = fetch_rows(selection, starts_at)
        selected = None if selection.replay_at else _forecast_hours(rows["forecasts"], times)
        if selected is None:
            source = OBSERVATIONS
            if not selection.replay_at:
                fallback = "Stored forecast incomplete, invalid or older than 24 hours. "
            selected = _observation_hours(rows["observations"], times, bool(selection.replay_at))
        intervals = [
            WeatherForecastInterval(
                starts_at=at,
                ends_at=at + timedelta(hours=1),
                solar_factor=solar_factor(row["value"], selected[0]["value"]),
                source=source,
            ).model_dump(mode="json")
            for at, row in zip(times, selected, strict=True)
        ]
        return SourceResult(
            source=source,
            source_time=starts_at,
            clock="replay" if selection.replay_at else "wall",
            data={
                "intervals": intervals,
                "input_times": [row["at"].isoformat() for row in selected],
                "updated_times": [row["updated_at"].isoformat() for row in selected]
                if source == STORED_FORECAST
                else [],
                "model_versions": sorted({row["model_version"] for row in selected})
                if source == STORED_FORECAST
                else [],
                "basis": "shortwave radiation ratio"
                if source == OBSERVATIONS
                else "capacity factor ratio",
                "fallback_reason": fallback.strip(),
            },
        )
    except (psycopg.Error, ValueError) as error:
        return SourceResult(
            status="unavailable",
            source=source,
            source_time=starts_at,
            clock="replay" if selection.replay_at else "wall",
            reason=fallback
            + ("Source weather DB unavailable" if isinstance(error, psycopg.Error) else str(error)),
        )
