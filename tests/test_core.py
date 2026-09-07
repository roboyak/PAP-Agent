import asyncio

from pap_agent.core import calculate, validate_candidate
from pap_agent.evidence import Evidence, acquire
from pap_agent.seed import sunny_fixture
from pap_agent.store import get_calculation, save_calculation


def test_sunny_energy_and_determinism():
    evidence = Evidence(status="valid", reason="fixture", scenario=sunny_fixture())
    first, second = calculate(evidence), calculate(evidence)
    assert first.status == "valid"
    assert first.pap.intervals == second.pap.intervals
    assert round(sum(item.energy_kwh for item in first.pap.intervals), 6) == 10.6
    assert first.battery_discharge_kwh == 0
    first.pap.intervals[0].available_kw = 100
    first.pap.intervals[0].energy_kwh = 100
    assert validate_candidate(evidence.scenario, first.forecast, first.pap.intervals)


def test_voltage_floor_withholds_additional_power():
    scenario = sunny_fixture()
    scenario.telemetry.battery_voltage_v = scenario.policy.min_battery_voltage_v
    result = calculate(Evidence(status="valid", reason="fixture", scenario=scenario))
    assert result.status == "withheld"
    assert result.pap.intervals == []
    assert "reserve floor" in result.validation[0]


def test_live_policy_and_calculation_persist(database, source_database):
    evidence = asyncio.run(acquire(database, "mysolark"))
    assert evidence.scenario.policy.min_battery_voltage_v == 305.2
    assert evidence.scenario.policy.max_extra_power_kw is None
    result = calculate(evidence)
    assert result.status == "valid"
    save_calculation(database, result.model_dump(mode="json"))
    assert get_calculation(database, result.id) == result.model_dump(mode="json")
