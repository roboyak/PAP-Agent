from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text

from pap_agent.config import Settings
from pap_agent.database import Database


@pytest.fixture
def empty_database_url():
    """Own a disposable database; never migrate or clear the development database."""
    admin = Database(Settings())
    name = f"pap_test_{uuid4().hex}"
    try:
        with admin.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.execute(text(f'CREATE DATABASE "{name}" TEMPLATE template0'))
            try:
                yield admin.engine.url.set(database=name).render_as_string(hide_password=False)
            finally:
                connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
    finally:
        admin.close()


@pytest.fixture
def database_url(empty_database_url, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", empty_database_url)
    command.upgrade(Config("alembic.ini"), "head")
    return empty_database_url


@pytest.fixture
def database(database_url):
    db = Database(Settings(database_url=database_url, _env_file=None))
    try:
        yield db
    finally:
        db.close()
