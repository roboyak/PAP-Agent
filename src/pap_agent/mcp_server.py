"""One local stdio process, two read-only source tools."""

from typing import Literal

from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from pydantic import AwareDatetime

from pap_agent.selection import RunSelection, Wing
from pap_agent.sources import SourceResult, telemetry_source, weather_source

server = MCPServer("PAP read-only sources")
READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=False)


@server.tool(annotations=READ_ONLY)
def get_current_telemetry(
    scenario: Literal["sunny", "mysolark"] = "sunny",
    wing: Wing = "1.24",
    replay_at: AwareDatetime | None = None,
) -> SourceResult:
    """Read a wing's latest scrape at/before replay_at, or now; preserve its recorded time."""
    return telemetry_source(scenario, RunSelection(wing=wing, replay_at=replay_at))


@server.tool(annotations=READ_ONLY)
def get_solar_forecast(
    starts_at: AwareDatetime,
    scenario: Literal["sunny", "mysolark"] = "sunny",
    wing: Wing = "1.24",
    replay_at: AwareDatetime | None = None,
) -> SourceResult:
    """Read stored weather for one wing's twelve-hour horizon; sunny alone is synthetic."""
    return weather_source(
        RunSelection(wing=wing, replay_at=replay_at), starts_at, scenario=scenario
    )


if __name__ == "__main__":
    server.run()
