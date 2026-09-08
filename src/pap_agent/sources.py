"""Read persisted MySolArk telemetry; weather is an explicit simulation."""

from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import NAMESPACE_URL, uuid5

import psycopg
from psycopg.rows import dict_row
from pydantic import AwareDatetime, BaseModel, Field

from pap_agent.config import Settings
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


def weather_source(starts_at: AwareDatetime) -> SourceResult:
    intervals = sunny_fixture().weather
    origin = intervals[0].starts_at
    for item in intervals:
        offset = item.starts_at - origin
        item.starts_at = starts_at + offset
        item.ends_at = item.starts_at + timedelta(hours=1)
    return SourceResult(
        source="Synthetic solar-factor fixture",
        source_time=starts_at,
        data={"intervals": [item.model_dump(mode="json") for item in intervals]},
    )
