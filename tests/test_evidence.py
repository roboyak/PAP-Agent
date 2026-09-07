import asyncio
from contextlib import asynccontextmanager
from datetime import timedelta

import pytest
from mcp import MCPError
from sqlalchemy import text

from pap_agent.evidence import acquire, validate_sources
from pap_agent.sources import telemetry_source, weather_source


def test_mcp_connection_failure_is_persisted_as_withheld(database, monkeypatch):
    @asynccontextmanager
    async def disconnected(*args, **kwargs):
        raise MCPError(-32000, "transport detail must stay private")
        yield  # pragma: no cover

    monkeypatch.setattr("pap_agent.evidence.Client", disconnected)
    evidence = asyncio.run(acquire(database))
    assert evidence.status == "withheld"
    with database.session() as session:
        payload = session.execute(text("SELECT payload FROM evidence_records")).scalar_one()
    assert payload["status"] == "withheld"
    assert "transport detail" not in str(payload)


def test_real_stdio_mcp_and_persisted_source_read(database, source_database):
    evidence = asyncio.run(acquire(database, "mysolark"))
    assert evidence.status == "valid", evidence.model_dump(mode="json")
    assert evidence.scenario.telemetry.data_mode == "live"
    assert evidence.scenario.telemetry.battery_voltage_v == 393
    assert 0 <= evidence.observed_age_seconds < 30
    assert {tool["name"] for tool in evidence.tools} == {
        "get_current_telemetry",
        "get_solar_forecast",
    }
    assert all(tool["annotations"]["read_only_hint"] for tool in evidence.tools)
    assert len(evidence.calls) == 2
    with database.session() as session:
        stored = session.execute(text("SELECT payload FROM evidence_records")).scalar_one()
    assert stored == evidence.model_dump(mode="json")


def test_t3_rejects_stale_evidence():
    telemetry = telemetry_source("sunny")
    weather = weather_source(telemetry.source_time)
    with pytest.raises(ValueError, match="stale"):
        validate_sources(telemetry, weather, telemetry.source_time + timedelta(minutes=6))
