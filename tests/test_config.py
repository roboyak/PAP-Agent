import pytest
from pydantic import ValidationError

from pap_agent.config import Settings


def test_local_defaults(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(_env_file=None)
    assert "@127.0.0.1:55432/pap" in settings.database_url.get_secret_value()
    assert "pap_local_only" not in repr(settings)


def test_database_url_environment(monkeypatch):
    url = "postgresql+psycopg://pap:test-secret@127.0.0.1:55432/other"
    monkeypatch.setenv("DATABASE_URL", url)
    settings = Settings(_env_file=None)
    assert settings.database_url.get_secret_value() == url
    assert "test-secret" not in str(settings)


@pytest.mark.parametrize(
    "url",
    [
        "not-a-url",
        "sqlite:///pap.db",
        "postgresql://pap:test-secret@localhost/pap",
        "postgresql+psycopg://pap:test-secret@localhost",
        "postgresql+psycopg://pap:test-secret@localhost:bad/pap",
    ],
)
def test_invalid_database_url_is_rejected_without_exposing_password(url):
    with pytest.raises(ValidationError) as exc:
        Settings(database_url=url, _env_file=None)
    assert "test-secret" not in str(exc.value)
