from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from psycopg.conninfo import make_conninfo
from sqlalchemy import text

from pap_agent.config import Settings
from pap_agent.database import Database


@pytest.fixture(autouse=True)
def deterministic_models(monkeypatch):
    monkeypatch.setenv("EMBEDDING_BACKEND", "test")
    monkeypatch.setenv("AGENT_BACKEND", "test")
    monkeypatch.setenv("ENABLE_INTERPRETATION_AGENT", "false")
    monkeypatch.setenv("PAP_PROFILE", "test")
    monkeypatch.setenv("ENABLE_LANGSMITH", "false")
    monkeypatch.setenv("CALIBRATION_BIAS_LIMIT_KW", "0.25")
    monkeypatch.setenv("CALIBRATION_DRIFT_LIMIT_KW", "0.25")
    monkeypatch.setenv("CALIBRATION_WINDOW_SAMPLES", "20")
    monkeypatch.setenv("CALIBRATION_REVIEW_DAYS", "7")
    monkeypatch.setenv("CALIBRATION_REVIEWED_AT", "1970-01-01T00:00:00Z")


@pytest.fixture
def source_database(database, monkeypatch):
    """Small source-shaped schema, isolated from PAP and the real source database."""
    with database.session() as session:
        session.execute(text("CREATE SCHEMA source_fixture"))
        session.execute(text("CREATE TABLE source_fixture.sites (name text, device_id text)"))
        session.execute(
            text("""CREATE TABLE source_fixture.telemetry_snapshots (
            device_id text, message_type text, timestamp timestamp,
            battery1_voltage float, solar_power_w float, load_power_w float)""")
        )
        session.execute(text("INSERT INTO source_fixture.sites VALUES ('DW 1.24', 'test-device')"))
        session.execute(
            text("""INSERT INTO source_fixture.telemetry_snapshots VALUES
            ('test-device', 'solark_cloud', CURRENT_TIMESTAMP AT TIME ZONE 'UTC', 393, 1560, 697)
        """)
        )
    url = database.engine.url
    monkeypatch.setenv(
        "SOURCE_DATABASE_DSN",
        make_conninfo(
            host=url.host,
            port=url.port,
            user=url.username,
            password=url.password,
            dbname=url.database,
            options="-c search_path=source_fixture",
        ),
    )


@pytest.fixture
def wing_history(database, source_database):
    """Two recorded points per wing plus latest readings; no production data."""
    with database.session() as session:
        for index, wing in enumerate(("1.21", "1.22", "1.23", "1.24", "1.25")):
            device = "test-device" if wing == "1.24" else f"test-{wing}"
            if wing != "1.24":
                session.execute(
                    text("INSERT INTO source_fixture.sites VALUES (:name, :device)"),
                    {"name": f"DW {wing}", "device": device},
                )
                session.execute(
                    text("""INSERT INTO source_fixture.telemetry_snapshots VALUES
                    (:device, 'solark_cloud', CURRENT_TIMESTAMP AT TIME ZONE 'UTC',
                     380, 2400, 500)"""),
                    {"device": device},
                )
            session.execute(
                text("""INSERT INTO source_fixture.telemetry_snapshots VALUES
                (:device, 'solark_cloud', '2026-08-30 18:58:00', 380, :solar, 500),
                (:device, 'solark_cloud', '2026-08-30 19:13:00', 381, :later_solar, 600)"""),
                {"device": device, "solar": 2100 + index * 100, "later_solar": 1800 + index * 100},
            )


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
