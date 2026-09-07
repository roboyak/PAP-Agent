from fastapi.testclient import TestClient

from pap_agent import __version__
from pap_agent.config import Settings
from pap_agent.main import create_app


def test_health_uses_postgresql_and_pgvector(database_url):
    with TestClient(create_app(Settings(database_url=database_url))) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "database": "ok", "pgvector": "ok"}


def test_missing_extension_is_not_healthy(empty_database_url):
    with TestClient(create_app(Settings(database_url=empty_database_url))) as client:
        response = client.get("/health")
        assert response.status_code == 503
        assert response.json() == {"status": "unavailable", "database": "ok", "pgvector": "missing"}


def test_unreachable_database_and_independent_version():
    settings = Settings(database_url="postgresql+psycopg://pap:test-secret@127.0.0.1:1/pap")
    with TestClient(create_app(settings)) as client:
        response = client.get("/health")
        assert response.status_code == 503
        assert response.json() == {
            "status": "unavailable",
            "database": "unavailable",
            "pgvector": "unavailable",
        }
        assert "test-secret" not in response.text
        version = client.get("/api/v1/version")
        assert version.status_code == 200
        assert version.json() == {"version": __version__, "read_only": True, "mode": "local"}
        assert client.post("/health").status_code == 405
