import asyncio
from uuid import uuid4

from pap_agent.core import calculate
from pap_agent.evidence import acquire
from pap_agent.publisher import publish
from pap_agent.store import save_calculation


def test_publisher_rechecks_t6_and_is_idempotent(database, monkeypatch):
    monkeypatch.setenv("CALIBRATION_BIAS_LIMIT_KW", "100")
    monkeypatch.setenv("CALIBRATION_DRIFT_LIMIT_KW", "100")
    evidence = asyncio.run(acquire(database, "sunny"))
    calculation = calculate(evidence)
    calculation.pap.intervals[0].available_kw = 100
    calculation.pap.intervals[0].energy_kwh = 100
    save_calculation(database, calculation.model_dump(mode="json"))
    episode_id = uuid4()
    result = publish(database, episode_id, evidence.id, calculation.id)
    assert result.status == "withheld"
    assert result.profile is None
    assert publish(database, episode_id, evidence.id, calculation.id) == result
