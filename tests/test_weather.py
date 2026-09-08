import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import psycopg
import pytest
from sqlalchemy import text

from pap_agent.calibration import calibration_report
from pap_agent.core import FORECAST_VERSION, STORED_WEATHER_VERSION, calculate, validate_candidate
from pap_agent.domain import TelemetrySnapshot
from pap_agent.evidence import acquire, validate_sources
from pap_agent.memory import index_memory, select_context
from pap_agent.outcomes import evaluate_publication, evaluate_sample
from pap_agent.selection import RunSelection
from pap_agent.sources import (
    OBSERVATIONS,
    STORED_FORECAST,
    _weather_rows,
    solar_factor,
    weather_source,
)
from pap_agent.store import (
    get_calculation,
    get_publication,
    get_scenario,
    save_evidence,
    save_scenario,
)
from pap_agent.workflow import run_episode

START = datetime(2026, 8, 30, 14, 37, tzinfo=UTC)  # 07:37 Pacific; intervals keep this anchor.
REPLAY = RunSelection(wing="1.21", replay_at=START)


def observations(values=None, age=timedelta(minutes=10)):
    return [
        {"at": START + timedelta(hours=i) - age, "value": value}
        for i, value in enumerate(values or [400, 800, 200, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    ]


def forecasts():
    return [
        {
            "at": START.replace(minute=0) + timedelta(hours=i),
            "value": value,
            "updated_at": START - timedelta(hours=1),
            "model_version": "test-open-meteo",
        }
        for i, value in enumerate([0.5, 0.8, 0.25, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    ]


def source(selection=REPLAY, *, observed=None, forecast=None):
    def fetch_rows(actual_selection, actual_start):
        assert actual_selection == selection and actual_start == START
        return {"observations": observed or [], "forecasts": forecast or []}

    return weather_source(selection, START, fetch_rows=fetch_rows)


@pytest.mark.parametrize(
    "value,reference,expected",
    [(200, 400, 0.5), (800, 400, 1), (0, 400, 0), (400, 0, 0), (0, 0, 0)],
)
def test_bounded_factor(value, reference, expected):
    assert solar_factor(value, reference) == expected


@pytest.mark.parametrize("value", [None, -1, float("nan"), float("inf")])
def test_invalid_weather_is_not_zero(value):
    with pytest.raises(ValueError):
        solar_factor(value, 400)
    with pytest.raises(ValueError):
        solar_factor(400, value)


def test_replay_preserves_cloud_and_night_and_ignores_forecasts():
    rows = observations()
    rows.append({"at": START + timedelta(seconds=1), "value": 999})
    result = source(observed=rows, forecast=forecasts())
    assert result.status == "ok"
    assert result.source == OBSERVATIONS and result.clock == "replay"
    assert result.data["input_times"][0] == (START - timedelta(minutes=10)).isoformat()
    assert [row["solar_factor"] for row in result.data["intervals"]] == [1, 1, 0.5] + [0] * 9
    assert {row["source"] for row in result.data["intervals"]} == {OBSERVATIONS}
    assert datetime.fromisoformat(result.data["intervals"][0]["starts_at"]) == START
    assert datetime.fromisoformat(result.data["intervals"][-1]["ends_at"]) == START + timedelta(
        hours=12
    )


def test_observation_tolerance_inclusive_and_whole_horizon_required():
    assert source(observed=observations(age=timedelta(minutes=90))).status == "ok"
    assert source(observed=observations()[:-1]).status == "ok"  # Last row is still only 70m old.
    for rows in (observations(age=timedelta(minutes=90, seconds=1)), observations()[:-2], []):
        result = source(observed=rows)
        assert result.status == "unavailable" and result.data == {}
        assert result.source == OBSERVATIONS
        assert "90 minutes" in result.reason


def test_live_forecast_prefers_complete_fresh_hour_buckets():
    result = source(RunSelection(), forecast=forecasts())
    assert result.status == "ok" and result.source == STORED_FORECAST
    assert result.data["intervals"][2]["solar_factor"] == 0.5
    assert result.data["model_versions"] == ["test-open-meteo"]
    assert result.data["input_times"][0] == START.replace(minute=0).isoformat()


@pytest.mark.parametrize("bad_forecast", ["missing", "stale", "future", "null_cf"])
def test_live_fallback_never_extends_observations_or_uses_future_actuals(bad_forecast):
    rows = forecasts()
    if bad_forecast == "missing":
        rows.pop()
    elif bad_forecast == "stale":
        rows[4]["updated_at"] = START - timedelta(hours=24, seconds=1)
    elif bad_forecast == "future":
        rows[4]["updated_at"] = START + timedelta(seconds=1)
    else:
        rows[4]["value"] = None
    result = source(RunSelection(), forecast=rows, observed=observations())
    assert result.status == "unavailable" and not result.data
    assert result.source == OBSERVATIONS
    assert "Stored forecast incomplete" in result.reason
    assert "90 minutes" in result.reason


def test_sunny_never_reads_source_database_and_db_errors_are_private():
    def failed(*args):
        raise psycopg.OperationalError("secret DSN and device identifier")

    fixture = weather_source(REPLAY, START, scenario="sunny", fetch_rows=failed)
    assert fixture.status == "ok" and fixture.source == "synthetic weather"
    assert {row["source"] for row in fixture.data["intervals"]} == {"synthetic weather"}
    result = weather_source(REPLAY, START, fetch_rows=failed)
    assert result.status == "unavailable" and result.reason == "Source weather DB unavailable"


def test_read_only_queries_keep_identifiers_inside_source_boundary(monkeypatch):
    class Connection:
        read_only = False
        queries = []

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def execute(self, query, args=None):
            assert self.read_only
            assert query.strip().startswith(("SELECT", "SET LOCAL statement_timeout"))
            self.queries.append((query, args))
            return self

        def fetchone(self):
            return {"n": 1}

        def fetchall(self):
            return []

    connection = Connection()

    def connect(*args, **kwargs):
        assert kwargs["connect_timeout"] == 3
        return connection

    monkeypatch.setattr("pap_agent.sources.psycopg.connect", connect)
    _weather_rows(REPLAY, START)
    assert connection.queries[0][0] == "SET LOCAL statement_timeout = 3000"
    assert all("%1.21%" in args for _, args in connection.queries[1:])
    assert "solar_forecast_hours" not in str(
        connection.queries
    )  # Replay ignores revised forecasts.


def test_weather_versions_preserve_old_scenario_and_t6(database, source_database):
    current = asyncio.run(acquire(database, "mysolark"))
    scenario = current.scenario
    legacy = scenario.model_copy(deep=True)
    legacy.name = scenario.name.rsplit("-w", 1)[0]
    legacy.label = "Saved MySolArk + synthetic weather"
    for row in legacy.weather:
        row.source, row.solar_factor = "synthetic weather", 0.25
    save_scenario(database, legacy)
    original = get_scenario(database, legacy.name).model_dump(mode="json")
    with database.session() as session:
        session.execute(
            text(
                "UPDATE source_fixture.solar_forecast_hours SET cf = 0.25 "
                "WHERE hour_utc = (SELECT max(hour_utc) FROM source_fixture.solar_forecast_hours)"
            )
        )
    updated = asyncio.run(acquire(database, "mysolark"))
    assert updated.scenario.name != scenario.name
    assert get_scenario(database, legacy.name).model_dump(mode="json") == original
    assert get_scenario(database, scenario.name) == scenario
    assert get_scenario(database, updated.scenario.name) == updated.scenario
    assert STORED_FORECAST in updated.scenario.label
    result = calculate(updated)
    assert STORED_FORECAST in result.pap.explanation
    updated.scenario.policy.max_extra_power_kw = 0.1
    result = calculate(updated)
    assert max(row.available_kw for row in result.pap.intervals) <= 0.1
    result.pap.intervals[0].available_kw = 1
    assert validate_candidate(updated.scenario, result.forecast, result.pap.intervals)


def test_missing_weather_is_published_as_withheld_without_touching_history(
    database, source_database
):
    first = asyncio.run(run_episode(database, "mysolark"))
    original = get_publication(database, first["publication_id"])
    with database.session() as session:
        session.execute(text("DELETE FROM source_fixture.solar_forecast_hours"))
    missing = asyncio.run(run_episode(database, "mysolark"))
    publication = get_publication(database, missing["publication_id"])
    assert publication["status"] == "withheld" and publication["profile"] is None
    assert "Stored forecast incomplete" in publication["reason"]
    assert get_publication(database, first["publication_id"]) == original
    assert missing["model_calls"] == 0


def test_t3_rejects_mixed_source_labels():
    from pap_agent.sources import telemetry_source

    telemetry = telemetry_source("sunny")
    weather = weather_source(RunSelection(), telemetry.source_time, scenario="sunny")
    weather.data["intervals"][1]["source"] = OBSERVATIONS
    with pytest.raises(ValueError, match="provenance"):
        validate_sources(telemetry, weather, telemetry.source_time)


def test_old_synthetic_weather_feedback_does_not_drive_new_forecasts(database, source_database):
    legacy = asyncio.run(acquire(database, "mysolark"))
    legacy.id = uuid4()
    legacy.scenario.name += "-legacy-fixture"
    legacy.scenario.label = "Pre-change MySolArk + synthetic weather"
    for row in legacy.scenario.weather:
        row.source = "synthetic weather"
    legacy.calls = []  # Constructed historical fixture, not a claim of source acquisition.
    save_evidence(database, legacy.model_dump(mode="json"))
    old = asyncio.run(run_episode(database, "mysolark", evidence_id=legacy.id))
    publication = get_publication(database, old["publication_id"])
    sample = TelemetrySnapshot.model_validate(publication["evidence"]["telemetry"])
    sample.id = uuid4()
    sample.observed_at += timedelta(seconds=1)
    sample.solar_power_kw = 0
    evaluate_sample(database, publication, sample)
    index_memory(database)
    assert calibration_report(database, "live", FORECAST_VERSION)["escalate"]
    new = asyncio.run(run_episode(database, "mysolark"))
    assert new["status"] == "valid" and new["reasoning_mode"] == "linear"
    assert new["model_calls"] == 0
    assert (
        get_calculation(database, new["calculation_id"])["forecast_version"]
        == STORED_WEATHER_VERSION
    )
    assert calibration_report(database, "live", STORED_WEATHER_VERSION)["samples"] == 0
    context = select_context(database, "live", STORED_WEATHER_VERSION)
    old_memory = [row for row in context["candidates"] if row["metadata"].get("kind") == "outcome"]
    assert old_memory and all(
        row["selection_reason"] == "wrong configuration/version" for row in old_memory
    )
    assert get_publication(database, old["publication_id"]) == publication


def test_fresh_outcome_does_not_require_future_weather(database, source_database):
    episode = asyncio.run(run_episode(database, "mysolark"))
    publication = get_publication(database, episode["publication_id"])
    with database.session() as session:
        session.execute(text("DELETE FROM source_fixture.solar_forecast_hours"))
        session.execute(
            text("""UPDATE source_fixture.telemetry_snapshots
            SET timestamp = CURRENT_TIMESTAMP AT TIME ZONE 'UTC', solar_power_w = 1000""")
        )
    outcome = asyncio.run(evaluate_publication(database, UUID(publication["id"])))
    assert outcome["metrics"]["solar_bias_kw"] == pytest.approx(0.56)
    assert outcome["calibration"]["forecast_version"] == STORED_WEATHER_VERSION
    assert outcome["calibration"]["samples"] == 1
    missing = asyncio.run(run_episode(database, "mysolark"))
    assert missing["status"] == "withheld"
    with database.session() as session:
        session.execute(
            text("""UPDATE source_fixture.telemetry_snapshots
            SET timestamp = timestamp - interval '10 minutes'""")
        )
    with pytest.raises(ValueError, match="stale"):
        asyncio.run(evaluate_publication(database, UUID(publication["id"])))
    assert get_publication(database, episode["publication_id"]) == publication
