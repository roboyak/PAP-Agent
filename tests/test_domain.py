from fastapi.testclient import TestClient
from sqlalchemy import text

from pap_agent.config import Settings
from pap_agent.main import create_app
from pap_agent.seed import sunny_fixture
from pap_agent.store import get_scenario, save_scenario


def test_persisted_fixture_is_typed_and_idempotent(database):
    fixture = sunny_fixture()
    save_scenario(database, fixture)
    save_scenario(database, fixture)
    assert get_scenario(database, "sunny") == fixture
    with database.session() as session:
        assert session.execute(text("SELECT count(*) FROM telemetry_snapshots")).scalar_one() == 1
        assert session.execute(text("SELECT count(*) FROM weather_intervals")).scalar_one() == 12


def test_scenario_api(database, database_url):
    save_scenario(database, sunny_fixture())
    with TestClient(create_app(Settings(database_url=database_url))) as client:
        assert client.get("/api/v1/scenarios").json() == [
            {"name": "sunny", "label": "Sunny demo (synthetic)"}
        ]
        response = client.get("/api/v1/scenarios/sunny")
        assert response.status_code == 200
        assert response.json()["telemetry"]["battery_voltage_v"] == 53.2
        assert len(response.json()["weather"]) == 12
