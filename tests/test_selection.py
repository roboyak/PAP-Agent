import asyncio
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, UUID, uuid5

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from pap_agent.config import Settings
from pap_agent.core import STORED_WEATHER_VERSION
from pap_agent.evidence import acquire
from pap_agent.main import create_app
from pap_agent.outcomes import calibration, evaluate_publication
from pap_agent.selection import WING_FLOORS, RunSelection
from pap_agent.store import get_publication
from pap_agent.workflow import run_episode

REPLAY_AT = datetime(2026, 8, 30, 19, tzinfo=UTC)


def test_read_all_wings_at_recorded_time(database, wing_history):
    async def exercise():
        ids = set()
        for index, (wing, floor) in enumerate(WING_FLOORS.items()):
            evidence = await acquire(
                database, "mysolark", selection=RunSelection(wing=wing, replay_at=REPLAY_AT)
            )
            assert evidence.status == "valid"
            assert evidence.observed_age_seconds == 120
            assert evidence.scenario.telemetry.source == f"DW {wing} MySolArk persisted scrape"
            assert evidence.scenario.telemetry.solar_power_kw == pytest.approx(2.1 + index * 0.1)
            assert evidence.scenario.policy.min_battery_voltage_v == floor
            assert evidence.calls[0]["arguments"]["wing"] == wing
            assert evidence.calls[1]["arguments"]["wing"] == wing
            assert evidence.calls[1]["result"]["source"] == "Open-Meteo stored observations"
            assert evidence.calls[0]["result"]["clock"] == "replay"
            if wing == "1.24":
                stamp = evidence.scenario.telemetry.observed_at.isoformat()
                assert evidence.scenario.telemetry.id == uuid5(
                    NAMESPACE_URL, f"pap:mysolark:{stamp}"
                )
            ids.add(evidence.scenario.telemetry.id)
        assert len(ids) == 5
        stale = await acquire(
            database,
            "mysolark",
            selection=RunSelection(wing="1.21", replay_at=REPLAY_AT.replace(minute=30)),
        )
        assert stale.status == "withheld"  # 19:13 is the latest before 19:30.
        assert stale.observed_age_seconds == 17 * 60

    asyncio.run(exercise())


def test_historical_clock_and_selection_survive_resume(database, wing_history):
    async def exercise():
        paused = await run_episode(
            database,
            "mysolark",
            selection=RunSelection(wing="1.21", replay_at=REPLAY_AT),
            interrupt_after=["acquire_evidence"],
        )
        result = await run_episode(database, episode_id=UUID(paused["episode_id"]))
        assert result["selection"] == paused["selection"]
        assert result["status"] == "valid"
        publication = get_publication(database, result["publication_id"])
        assert publication["selection"] == result["selection"]
        assert publication["observed_age_seconds"] == 120
        assert datetime.fromisoformat(publication["generated_at"]) > REPLAY_AT
        assert publication["profile"]["intervals"][0]["available_kw"] == 1.6
        assert publication["feedback"] is None
        with pytest.raises(ValueError, match="does not update live"):
            await evaluate_publication(database, UUID(publication["id"]))

    asyncio.run(exercise())
    with TestClient(create_app(Settings())) as client:
        assert (
            client.post(
                "/api/v1/pap/run",
                json={"scenario": "mysolark", "replay_at": "2026-09-06T00:00:00-07:00"},
            ).status_code
            == 422
        )


def test_latest_outcome_uses_selected_wing_and_separate_feedback(database, wing_history):
    async def exercise():
        result = await run_episode(database, "mysolark", selection=RunSelection(wing="1.21"))
        with database.session() as session:
            session.execute(
                text("""UPDATE source_fixture.telemetry_snapshots
                SET solar_power_w = 1200, timestamp = CURRENT_TIMESTAMP AT TIME ZONE 'UTC'
                WHERE device_id = 'test-1.21' AND timestamp > '2026-09-01'""")
            )
        feedback = await evaluate_publication(database, UUID(result["publication_id"]))
        assert feedback["outcome"]["sample"]["source"].startswith("DW 1.21 ")
        assert feedback["calibration"]["samples"] == 1
        version = STORED_WEATHER_VERSION
        assert calibration(database, "live:1.21", version)["mean_solar_bias_kw"] == 1.2
        assert calibration(database, "live:1.22", version) is None
        assert calibration(database, "live", version) is None

    asyncio.run(exercise())
