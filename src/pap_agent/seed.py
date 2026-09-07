from datetime import UTC, datetime, timedelta
from uuid import NAMESPACE_URL, uuid5

from pap_agent.config import Settings
from pap_agent.database import Database
from pap_agent.domain import ReservePolicy, Scenario, TelemetrySnapshot, WeatherForecastInterval
from pap_agent.store import save_scenario


def sunny_fixture() -> Scenario:
    start = datetime(2026, 9, 7, 12, tzinfo=UTC)
    return Scenario(
        name="sunny",
        label="Sunny demo (synthetic)",
        telemetry=TelemetrySnapshot(
            id=uuid5(NAMESPACE_URL, "pap:synthetic:sunny"),
            observed_at=start,
            battery_voltage_v=53.2,
            solar_power_kw=4.0,
            load_power_kw=1.5,
            source="synthetic fixture",
        ),
        weather=[
            WeatherForecastInterval(
                starts_at=start + timedelta(hours=hour),
                ends_at=start + timedelta(hours=hour + 1),
                solar_factor=factor,
            )
            for hour, factor in enumerate([1, 1, 0.9, 0.8, 0.7, 0.5, 0.3, 0.1, 0, 0, 0, 0])
        ],
        policy=ReservePolicy(),
    )


if __name__ == "__main__":
    database = Database(Settings())
    try:
        save_scenario(database, sunny_fixture())
        print("Sunny fixture is stored (existing rows preserved).")
    finally:
        database.close()
