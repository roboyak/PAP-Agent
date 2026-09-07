"""One local stdio process, two read-only source tools."""

from typing import Literal

from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from pydantic import AwareDatetime

from pap_agent.sources import SourceResult, telemetry_source, weather_source

server = MCPServer("PAP read-only sources")
READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=False)


@server.tool(annotations=READ_ONLY)
def get_current_telemetry(scenario: Literal["sunny", "mysolark"] = "sunny") -> SourceResult:
    """Read latest persisted MySolArk scrape with its real timestamp, or a synthetic fixture."""
    return telemetry_source(scenario)


@server.tool(annotations=READ_ONLY)
def get_solar_forecast(starts_at: AwareDatetime) -> SourceResult:
    """Read twelve synthetic hourly solar factors. This is not a live weather forecast."""
    return weather_source(starts_at)


if __name__ == "__main__":
    server.run()
