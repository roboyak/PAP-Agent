from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import text

from pap_agent import observability
from pap_agent.config import Settings
from pap_agent.main import create_app


@pytest.mark.parametrize("provider", ["openai", "anthropic"])
def test_cloud_readiness_checks_configuration_only(database_url, provider):
    settings = Settings(
        _env_file=None,
        database_url=database_url,
        agent_backend=provider,
        agent_model="configured-model",
        openai_api_key=None,
        anthropic_api_key=None,
    )
    with TestClient(create_app(settings)) as client:
        result = client.get("/health/ready")
        assert result.status_code == 503
        assert result.json()["checks"]["cloud_api_key_configured"] is False
    setattr(settings, f"{provider}_api_key", SecretStr("local-test-key"))
    with TestClient(create_app(settings)) as client:
        result = client.get("/health/ready")
        assert result.status_code == 200
        assert result.json()["agent_model"] == "configured-model"
        assert result.json()["model_backend"] == provider
        assert "Configuration only" in result.json()["model_check"]
        assert "local-test-key" not in result.text


def test_ready_checks_dependencies_without_persisting_probe_evidence(database, database_url):
    with TestClient(create_app(Settings(database_url=database_url))) as client:
        assert client.get("/health/live").json() == {"status": "ok"}
        result = client.get("/health/ready")
        assert result.status_code == 200
        assert result.json()["status"] == "ready"
        assert all(result.json()["checks"].values())
        assert result.json()["model_backend"] == "test"
        with database.session() as session:
            assert session.execute(text("SELECT count(*) FROM evidence_records")).scalar_one() == 0
            assert session.execute(text("SELECT count(*) FROM reasoning_records")).scalar_one() == 0
        assert 'data-default-source="sunny"' in client.get("/").text
        assert client.post("/api/v1/pap/run", json={}).json()["status"] == "valid"


def test_missing_migrations_not_ready_but_live(empty_database_url):
    with TestClient(create_app(Settings(database_url=empty_database_url))) as client:
        assert client.get("/health/live").status_code == 200
        response = client.get("/health/ready")
        assert response.status_code == 503
        assert response.json()["checks"]["database_checkpointer"] is False


def test_optional_export_is_allowlisted_and_failure_nonfatal(monkeypatch, caplog, tmp_path):
    captured = []
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_PROJECT", raising=False)
    (tmp_path / ".env").write_text(
        "LANGSMITH_API_KEY=local-test-key\nLANGSMITH_PROJECT=local-test-project\n"
    )

    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs["api_key"] == "local-test-key"

        def create_run(self, *args, **kwargs):
            captured.append(kwargs)

        def close(self, **kwargs):
            pass

    monkeypatch.setattr(observability, "Client", FakeClient)
    episode = {
        "episode_id": str(uuid4()),
        "publication_id": str(uuid4()),
        "status": "valid",
        "scenario": "sunny",
        "reasoning_mode": "linear",
        "model_calls": 0,
        "private_data": "never-export-this",
    }
    observability.export_summary(episode)
    assert captured == []
    monkeypatch.setenv("ENABLE_LANGSMITH", "true")
    observability.export_summary(episode)
    assert "never-export-this" not in str(captured)
    assert captured[0]["tags"] == ["test", "sunny"]
    assert captured[0]["project_name"] == "local-test-project"
    assert "local-test-key" not in str(captured)

    def unavailable(*args, **kwargs):
        raise ConnectionError("sensitive-provider-detail")

    monkeypatch.setattr(FakeClient, "create_run", unavailable)
    observability.export_summary(episode)
    assert "Optional summary export unavailable" in caplog.text
    assert "sensitive-provider-detail" not in caplog.text
