import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from pap_agent.calibration import calibration_report
from pap_agent.core import FORECAST_VERSION
from pap_agent.domain import TelemetrySnapshot
from pap_agent.outcomes import evaluate_publication, evaluate_sample
from pap_agent.reasoning import get_record
from pap_agent.selection import RunSelection
from pap_agent.store import get_publication
from pap_agent.workflow import run_episode


def test_recent_error_drift_and_explicit_retuning(database, monkeypatch):
    monkeypatch.setenv("CALIBRATION_WINDOW_SAMPLES", "2")
    monkeypatch.setenv("CALIBRATION_BIAS_LIMIT_KW", "0.5")
    episode = asyncio.run(run_episode(database, "sunny"))
    publication = get_publication(database, episode["publication_id"])
    sample = TelemetrySnapshot.model_validate(publication["evidence"]["telemetry"])
    for index, bias in enumerate([3, 0, 0, 0.3, 0.3], 1):
        sample.id = uuid4()
        sample.observed_at = datetime(2026, 9, 7, 12, index, tzinfo=UTC)
        sample.solar_power_kw = 4 - bias
        evaluate_sample(database, publication, sample)
    report = calibration_report(database, "synthetic", FORECAST_VERSION)
    assert report["samples"] == report["comparison_samples"] == 2
    assert len(report["outcome_ids"]) == 4
    assert report["mean_solar_bias_kw"] == pytest.approx(0.3)
    assert report["error_drift_kw"] == pytest.approx(0.3)
    assert report["signals"] == ["error_drift"]
    assert report["escalate"] and report["review_due"]
    assert report["ece"]["status"] == "unavailable"
    # A review timestamp does not make an observed alarm disappear.
    monkeypatch.setenv("CALIBRATION_REVIEWED_AT", datetime.now(UTC).isoformat())
    reviewed = calibration_report(database, "synthetic", FORECAST_VERSION)
    assert not reviewed["review_due"]
    assert reviewed["signals"] == ["error_drift"] and reviewed["review_required"]
    monkeypatch.setenv("CALIBRATION_DRIFT_LIMIT_KW", "0.4")
    changed = calibration_report(database, "synthetic", FORECAST_VERSION)
    assert not changed["escalate"]
    assert changed["policy_id"] != report["policy_id"]
    assert changed["outcome_ids"] == report["outcome_ids"]
    assert changed["mean_solar_bias_kw"] == report["mean_solar_bias_kw"]


def test_live_feedback_expires_and_stays_with_its_wing(database, wing_history):
    episode = asyncio.run(run_episode(database, "mysolark", selection=RunSelection(wing="1.21")))
    publication = get_publication(database, episode["publication_id"])
    sample = TelemetrySnapshot.model_validate(publication["evidence"]["telemetry"])
    sample.id = uuid4()
    sample.observed_at += timedelta(seconds=1)
    sample.solar_power_kw = 0
    evaluate_sample(database, publication, sample)
    now = sample.observed_at + timedelta(minutes=1)
    fresh = calibration_report(database, "live:1.21", FORECAST_VERSION, now=now)
    assert fresh["samples"] == 1 and fresh["escalate"]
    assert fresh["drift_status"] == "insufficient_data"
    assert calibration_report(database, "live:1.22", FORECAST_VERSION, now=now)["samples"] == 0
    assert calibration_report(database, "live:1.21", "other-version", now=now)["samples"] == 0
    expired = calibration_report(
        database, "live:1.21", FORECAST_VERSION, now=now + timedelta(days=8)
    )
    assert expired["stale"] and expired["review_required"]
    assert expired["mean_solar_bias_kw"] is None and not expired["escalate"]
    assert expired["confidence"] == "low"


def test_threshold_snapshot_survives_resume_and_preserves_power(database, monkeypatch):
    async def exercise():
        initial = await run_episode(database, "sunny")
        original = get_publication(database, initial["publication_id"])
        await evaluate_publication(database, UUID(initial["publication_id"]))
        paused = await run_episode(database, "sunny", interrupt_after=["assess_ambiguity"])
        frozen = get_record(database, paused["assessment_id"])["feedback"]
        assert frozen["policy"]["bias_limit_kw"] == 0.25
        monkeypatch.setenv("CALIBRATION_BIAS_LIMIT_KW", "3")
        resumed = await run_episode(database, episode_id=UUID(paused["episode_id"]))
        preserved = get_publication(database, resumed["publication_id"])
        assert preserved["feedback"] == frozen
        assert resumed["reasoning_mode"] == "selective_tot"
        newer = await run_episode(database, "sunny")
        current = get_publication(database, newer["publication_id"])
        assert newer["reasoning_mode"] == "linear"
        assert current["feedback"]["policy"]["bias_limit_kw"] == 3
        assert current["feedback"]["policy_id"] != frozen["policy_id"]
        assert current["profile"]["confidence"] == "reduced"
        assert preserved["profile"]["confidence"] == "low"
        assert (
            preserved["profile"]["intervals"]
            == current["profile"]["intervals"]
            == original["profile"]["intervals"]
        )
        assert current["evidence"]["policy"] == original["evidence"]["policy"]

    asyncio.run(exercise())
