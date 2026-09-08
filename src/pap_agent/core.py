"""T4 forecast → T5 solar surplus → T6 hard checks. No model owns these numbers."""

from datetime import UTC, datetime
from math import isclose
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from pap_agent.domain import PAP, ForecastInterval, PowerAvailabilityInterval, Scenario
from pap_agent.evidence import Evidence

FORECAST_VERSION = "solar-persistence-demo-v1"
STORED_WEATHER_VERSION = "solar-persistence-stored-weather-v1"


class Calculation(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    evidence_id: UUID
    status: Literal["valid", "withheld"] = "withheld"
    forecast_version: str = FORECAST_VERSION
    forecast: list[ForecastInterval] = Field(default_factory=list)
    pap: PAP | None = None
    validation: list[str] = Field(default_factory=list)
    battery_discharge_kwh: float = 0


def forecast(scenario: Scenario) -> list[ForecastInterval]:
    return [
        ForecastInterval(
            starts_at=item.starts_at,
            ends_at=item.ends_at,
            generation_kw=round(scenario.telemetry.solar_power_kw * item.solar_factor, 6),
            demand_kw=scenario.telemetry.load_power_kw,
        )
        for item in scenario.weather
    ]


def availability(
    scenario: Scenario, forecasts: list[ForecastInterval]
) -> list[PowerAvailabilityInterval]:
    result = []
    for item in forecasts:
        power = max(0, item.generation_kw - item.demand_kw)
        if scenario.policy.max_extra_power_kw is not None:
            power = min(power, scenario.policy.max_extra_power_kw)
        hours = (item.ends_at - item.starts_at).total_seconds() / 3600
        result.append(
            PowerAvailabilityInterval(
                starts_at=item.starts_at,
                ends_at=item.ends_at,
                available_kw=round(power, 6),
                energy_kwh=round(power * hours, 6),
            )
        )
    return result


def validate_candidate(
    scenario: Scenario,
    forecasts: list[ForecastInterval],
    intervals: list[PowerAvailabilityInterval],
) -> list[str]:
    if scenario.telemetry.battery_voltage_v <= scenario.policy.min_battery_voltage_v:
        return ["Battery voltage is at or below the reserve floor"]
    if len(intervals) != 12 or len(forecasts) != 12:
        return ["Expected twelve hourly intervals"]
    for expected, actual in zip(availability(scenario, forecasts), intervals, strict=True):
        if (
            actual.starts_at != expected.starts_at
            or actual.ends_at != expected.ends_at
            or (not 0 <= actual.available_kw <= expected.available_kw)
            or not isclose(
                actual.energy_kwh,
                actual.available_kw * ((actual.ends_at - actual.starts_at).total_seconds() / 3600),
                abs_tol=1e-6,
            )
        ):
            return ["Candidate exceeds solar surplus/cap or has inconsistent energy units"]
    return []


def calculate(evidence: Evidence, calculation_id: UUID | None = None) -> Calculation:
    result = Calculation(id=calculation_id or uuid4(), evidence_id=evidence.id)
    scenario = evidence.scenario
    if evidence.status != "valid" or scenario is None:
        result.validation = ["T3 did not accept the evidence"]
        return result
    if scenario.weather_source != "synthetic weather":
        result.forecast_version = STORED_WEATHER_VERSION
    if (
        scenario.telemetry.data_mode == "live"
        and not 0
        <= (
            (evidence.selection.replay_at or datetime.now(UTC)) - scenario.telemetry.observed_at
        ).total_seconds()
        <= 300
    ):
        result.validation = ["Evidence became stale before calculation"]
        return result
    result.forecast = forecast(scenario)
    intervals = availability(scenario, result.forecast)
    result.validation = validate_candidate(scenario, result.forecast, intervals)
    result.status = "withheld" if result.validation else "valid"
    result.pap = PAP(
        id=result.id,
        telemetry_id=scenario.telemetry.id,
        policy_id=scenario.policy.id,
        status=result.status,
        intervals=intervals if result.status == "valid" else [],
        confidence="reduced",
        explanation=(
            f"Evaluation baseline: {scenario.weather_source}; "
            "constant measured demand; solar surplus only; "
            "zero battery discharge. Voltage floor gates additional power. "
            "Future voltage and equipment capability are not predicted."
            + (
                " Replay uses actual weather across the horizon, not an as-of forecast."
                if evidence.selection.replay_at and scenario.weather_source != "synthetic weather"
                else ""
            )
        ),
    )
    return result
