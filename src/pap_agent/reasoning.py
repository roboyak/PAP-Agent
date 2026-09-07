"""Small canonical audit store. A reserved model attempt is never retried on resume."""

import json

from fastapi.encoders import jsonable_encoder
from sqlalchemy import text

from pap_agent.database import Database


def get_record(database: Database, record_id) -> dict | None:
    with database.session() as session:
        return session.execute(
            text("SELECT payload FROM reasoning_records WHERE id = :id"), {"id": record_id}
        ).scalar_one_or_none()


def save_record(database: Database, record: dict, *, finish=False) -> bool:
    with database.session() as session:
        conflict = "DO UPDATE SET payload = EXCLUDED.payload" if finish else "DO NOTHING"
        return (
            session.execute(
                text(
                    "INSERT INTO reasoning_records (id, episode_id, kind, payload) "
                    "VALUES (:id, :episode_id, :kind, CAST(:payload AS jsonb)) "
                    f"ON CONFLICT (id) {conflict} RETURNING id"
                ),
                {**record, "payload": json.dumps(jsonable_encoder(record))},
            ).scalar_one_or_none()
            is not None
        )


def episode_records(database: Database, episode_id) -> list[dict]:
    with database.session() as session:
        return list(
            session.execute(
                text(
                    "SELECT payload FROM reasoning_records WHERE episode_id = :id ORDER BY kind, id"
                ),
                {"id": episode_id},
            ).scalars()
        )


def model_call_count(database: Database, episode_id) -> int:
    return sum(record.get("calls", 0) for record in episode_records(database, episode_id))
