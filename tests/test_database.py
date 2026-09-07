import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text

from pap_agent.config import Settings
from pap_agent.database import Database


def test_migrate_empty_database_and_non_destructive_reapply(empty_database_url, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", empty_database_url)
    db = Database(Settings())
    config = Config("alembic.ini")
    try:
        assert db.has_pgvector() is False
        command.upgrade(config, "head")
        command.upgrade(config, "head")
        assert db.has_pgvector() is True
        with db.session() as session:
            assert session.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one() == ("0001_enable_pgvector")
            assert (
                session.execute(text("SELECT '[1,0,0]'::vector <=> '[1,0,0]'::vector")).scalar_one()
                == 0
            )
        command.downgrade(config, "base")
        assert db.has_pgvector() is True  # Downgrade deliberately retains the shared extension.
        command.upgrade(config, "head")
        assert db.has_pgvector() is True
    finally:
        db.close()


def test_sessions_commit_success_and_roll_back_failure(database):
    with database.session() as session:
        session.execute(text("CREATE TABLE session_probe (id integer PRIMARY KEY)"))
        session.execute(text("INSERT INTO session_probe VALUES (1)"))
    with pytest.raises(RuntimeError, match="abort"):
        with database.session() as session:
            session.execute(text("INSERT INTO session_probe VALUES (2)"))
            raise RuntimeError("abort")
    with database.session() as session:
        assert session.execute(text("SELECT id FROM session_probe")).scalars().all() == [1]
