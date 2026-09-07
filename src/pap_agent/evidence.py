"""T1/T2 acquire through MCP; T3 validates before numerical work."""

import asyncio
import sys
from datetime import UTC, datetime
from time import perf_counter
from typing import Literal
from uuid import UUID, uuid4

from mcp import Client, MCPError, StdioServerParameters
from pydantic import BaseModel, Field, ValidationError

from pap_agent.config import Settings
from pap_agent.database import Database
from pap_agent.domain import ReservePolicy, Scenario, TelemetrySnapshot, WeatherForecastInterval
from pap_agent.sources import SourceResult
from pap_agent.store import save_evidence, save_scenario


class Evidence(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    status: Literal["valid", "withheld"]
    reason: str
    observed_age_seconds: float | None = None
    scenario: Scenario | None = None
    tools: list[dict] = Field(default_factory=list)
    calls: list[dict] = Field(default_factory=list)


def validate_sources(telemetry: SourceResult, weather: SourceResult, now: datetime) -> Scenario:
    if telemetry.status != "ok" or weather.status != "ok":
        raise ValueError("Source unavailable")
    snapshot = TelemetrySnapshot.model_validate(telemetry.data)
    if (
        snapshot.observed_at != telemetry.source_time
        or weather.source_time != telemetry.source_time
    ):
        raise ValueError("Source timestamps disagree")
    if not 0 <= (now - snapshot.observed_at).total_seconds() <= 300:
        raise ValueError("Telemetry stale or ahead of evaluation clock")
    intervals = [WeatherForecastInterval.model_validate(item) for item in weather.data["intervals"]]
    if len(intervals) != 12 or intervals[0].starts_at != weather.source_time:
        raise ValueError("Weather does not cover the twelve-hour horizon")
    for index, item in enumerate(intervals):
        if (item.ends_at - item.starts_at).total_seconds() != 3600 or (
            index and intervals[index - 1].ends_at != item.starts_at
        ):
            raise ValueError("Weather intervals must be contiguous hours")
    live = snapshot.data_mode == "live"
    return Scenario(
        name=f"mysolark-{snapshot.id.hex[:8]}-{Settings().battery_floor_v}" if live else "sunny",
        label="MySolArk live scrape + synthetic weather" if live else "Sunny demo (synthetic)",
        telemetry=snapshot,
        weather=intervals,
        policy=ReservePolicy(
            id=f"dw-floor-{Settings().battery_floor_v}",
            label=(
                "Fixed observed-minimum floor; user maps to ~30% SOC reserve. "
                "No equipment cap configured."
            ),
            min_battery_voltage_v=Settings().battery_floor_v,
            max_extra_power_kw=None,
        )
        if live
        else ReservePolicy(),
    )


async def acquire(database: Database, scenario: str = "sunny") -> Evidence:
    calls, tools, age = [], [], None
    try:
        async with (
            asyncio.timeout(10),
            Client(
                StdioServerParameters(
                    command=sys.executable,
                    args=["-m", "pap_agent.mcp_server"],
                    env={"SOURCE_DATABASE_DSN": Settings().source_database_dsn.get_secret_value()},
                ),
                read_timeout_seconds=5,
            ) as client,
        ):
            tools = [item.model_dump(mode="json") for item in (await client.list_tools()).tools]

            async def call(name, arguments):
                started = perf_counter()
                result = await client.call_tool(name, arguments)
                output = result.structured_content
                calls.append(
                    {
                        "tool": name,
                        "arguments": arguments,
                        "result": output,
                        "duration_ms": round((perf_counter() - started) * 1000),
                    }
                )
                if result.is_error:
                    raise ValueError("MCP source unavailable")
                return SourceResult.model_validate(output)

            telemetry = await call("get_current_telemetry", {"scenario": scenario})
            now = datetime.now(UTC) if telemetry.clock == "wall" else telemetry.source_time
            age = round((now - telemetry.source_time).total_seconds(), 1)
            weather = await call(
                "get_solar_forecast",
                {
                    "starts_at": telemetry.source_time.isoformat(),
                },
            )
        record = validate_sources(telemetry, weather, now)
        save_scenario(database, record)
        evidence = Evidence(
            status="valid",
            reason=f"T3 passed at {telemetry.clock} clock",
            observed_age_seconds=age,
            scenario=record,
            tools=tools,
            calls=calls,
        )
    except* (ValueError, ValidationError, TimeoutError, KeyError, MCPError):
        evidence = Evidence(
            status="withheld",
            reason="Source unavailable or T3 validation failed",
            observed_age_seconds=age,
            tools=tools,
            calls=calls,
        )
    save_evidence(database, evidence.model_dump(mode="json"))
    return evidence
