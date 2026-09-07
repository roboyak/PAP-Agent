"""Small local readiness probe; no model generation or persistent probe evidence."""

import json
from pathlib import Path
from uuid import uuid4

import httpx
from alembic.config import Config
from alembic.script import ScriptDirectory
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import Error as PostgresError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from pap_agent.config import Settings
from pap_agent.database import Database
from pap_agent.evidence import acquire
from pap_agent.workflow import build_graph, checkpoint_dsn


async def readiness(database: Database, settings: Settings) -> dict:
    checks = {}
    try:
        root = Path(__file__).resolve().parents[2]
        head = ScriptDirectory.from_config(Config(root / "alembic.ini")).get_current_head()
        with database.session() as session:
            checks["migrations"] = (
                session.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                == head
            )
            checks["pgvector"] = (
                session.execute(text("SELECT '[1,0]'::vector <=> '[1,0]'::vector")).scalar_one()
                == 0
            )
            session.execute(
                text(
                    "SELECT id FROM semantic_memory ORDER BY embedding <=> "
                    "CAST(:query AS vector) LIMIT 1"
                ),
                {"query": json.dumps([1.0] + [0.0] * 767)},
            ).first()
            checks["semantic_query"] = True
            probe_id = uuid4()
            probe = session.begin_nested()
            checks["writable"] = (
                session.execute(
                    text(
                        "INSERT INTO reasoning_records (id, episode_id, kind, payload) "
                        "VALUES (:id, :id, 'readiness', '{}'::jsonb) RETURNING id"
                    ),
                    {"id": probe_id},
                ).scalar_one()
                == probe_id
            )
            probe.rollback()
        async with AsyncPostgresSaver.from_conn_string(checkpoint_dsn(database)) as saver:
            await saver.setup()
            await saver.aget_tuple({"configurable": {"thread_id": "readiness"}})
            build_graph(database, saver)
            checks["graph_checkpointer"] = True
    except (SQLAlchemyError, PostgresError):
        checks["database_checkpointer"] = False
    scenario = "mysolark" if settings.pap_profile == "development" else "sunny"
    evidence = await acquire(database, scenario, persist=False)
    checks["source_freshness"] = evidence.status == "valid"
    checks["mcp_read_only_contract"] = {tool["name"] for tool in evidence.tools} == {
        "get_current_telemetry",
        "get_solar_forecast",
    } and all(
        tool["annotations"]["read_only_hint"] is True
        and tool["annotations"]["destructive_hint"] is False
        for tool in evidence.tools
    )
    checks["models"] = True
    if settings.agent_backend in {"openai", "anthropic"}:
        key = (
            settings.openai_api_key
            if settings.agent_backend == "openai"
            else settings.anthropic_api_key
        )
        checks["cloud_api_key_configured"] = bool(key)
    if settings.agent_backend == "ollama" or settings.embedding_backend == "ollama":
        try:
            response = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=3, trust_env=False)
            response.raise_for_status()
            installed = {model["name"] for model in response.json()["models"]}
            required = ({settings.agent_model} if settings.agent_backend == "ollama" else set()) | (
                {settings.embedding_model} if settings.embedding_backend == "ollama" else set()
            )
            checks["models"] = required <= installed
        except (httpx.HTTPError, ValueError, KeyError):
            checks["models"] = False
    return {
        "status": "ready" if all(checks.values()) else "unavailable",
        "checks": checks,
        "profile": settings.pap_profile,
        "source": scenario,
        "interpretation_enabled": settings.enable_interpretation_agent,
        "model_backend": settings.agent_backend,
        "agent_model": settings.agent_model if settings.agent_backend != "test" else "test-double",
        "model_check": "Configuration only; cloud access is checked on a model call."
        if settings.agent_backend in {"openai", "anthropic"}
        else "Local model availability",
        "embedding_backend": settings.embedding_backend,
        "evidence_age_seconds": evidence.observed_age_seconds,
    }
