"""Small PAP contracts. Units are part of each field name; SOC is intentionally absent."""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class TelemetrySnapshot(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    id: UUID = Field(default_factory=uuid4)
    observed_at: AwareDatetime
    battery_voltage_v: float = Field(gt=0)
    solar_power_kw: float = Field(ge=0)
    load_power_kw: float = Field(ge=0)
    source: str
    data_mode: Literal["synthetic", "live"] = "synthetic"
    measurement_time_verified: bool = False


class Interval(BaseModel):
    starts_at: AwareDatetime
    ends_at: AwareDatetime


class WeatherForecastInterval(Interval):
    solar_factor: float = Field(ge=0, le=1)
    source: str = "synthetic weather"


class ReservePolicy(BaseModel):
    id: str = "demo-v1"
    label: str = "Synthetic demo policy; not equipment ratings"
    min_battery_voltage_v: float = Field(default=48.0, gt=0)
    max_extra_power_kw: float | None = Field(default=5.0, gt=0)


class Scenario(BaseModel):
    name: str
    label: str
    telemetry: TelemetrySnapshot
    weather: list[WeatherForecastInterval]
    policy: ReservePolicy

    @property
    def weather_source(self) -> str:
        return " + ".join(dict.fromkeys(item.source for item in self.weather))


class ForecastInterval(Interval):
    generation_kw: float = Field(ge=0, allow_inf_nan=False)
    demand_kw: float = Field(ge=0, allow_inf_nan=False)


class PowerAvailabilityInterval(Interval):
    available_kw: float = Field(ge=0)
    energy_kwh: float = Field(ge=0)


class PAP(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    telemetry_id: UUID
    policy_id: str
    status: Literal["valid", "withheld"]
    intervals: list[PowerAvailabilityInterval] = Field(default_factory=list)
    confidence: Literal["baseline", "reduced", "low"] = "baseline"
    explanation: str = ""


class AgentEpisodeRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    pap_id: UUID | None = None
    started_at: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    reasoning_mode: Literal["linear", "selective_tot"] = "linear"
    stop_reason: str = ""
