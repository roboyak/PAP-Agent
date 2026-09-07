import asyncio
from uuid import UUID, uuid4

from sqlalchemy import text

from pap_agent.agents import Advice, call_agent, validated_advice
from pap_agent.comparison import compare_agents
from pap_agent.memory import index_memory, select_context
from pap_agent.reasoning import episode_records
from pap_agent.store import get_publication
from pap_agent.workflow import run_episode


def test_paired_runs_preserve_power_and_agent_resume(database):
    index_memory(database)
    result = asyncio.run(compare_agents(database, "sunny"))
    assert result["same_available_power"]
    off, on = result["runs"]
    assert (off["model_calls"], on["model_calls"]) == (0, 1)
    assert off["episode"]["evidence_id"] == on["episode"]["evidence_id"]
    publication = get_publication(database, on["episode"]["publication_id"])
    assert publication["interpretation"]["accepted"]
    assert publication["profile"]["confidence"] == "low"
    paused = asyncio.run(
        run_episode(
            database,
            "sunny",
            interpretation_enabled=True,
            interrupt_after=["grounded_interpretation"],
        )
    )
    resumed = asyncio.run(run_episode(database, episode_id=UUID(paused["episode_id"])))
    assert resumed["model_calls"] == 1
    assert len(episode_records(database, resumed["episode_id"])) == 3


def test_malformed_authority_and_unknown_citations_are_rejected(database):
    context = {"evidence_id": "actual-id"}
    fixture = {
        "evidence_ids": ["invented-id"],
        "confidence": "lower",
        "fallback": "none",
        "re_evaluate": False,
        "explanation": "Unsupported citation",
        "insufficient": False,
    }
    record = asyncio.run(
        call_agent(database, uuid4(), uuid4(), "interpretation", context, Advice, fixture)
    )
    assert validated_advice(record, "actual-id", []) is None
    fixture["available_kw"] = 999
    record = asyncio.run(
        call_agent(database, uuid4(), uuid4(), "interpretation", context, Advice, fixture)
    )
    assert record["status"] == "unavailable" and record["output"] is None
    blocked = asyncio.run(
        call_agent(
            database, uuid4(), uuid4(), "interpretation", context, Advice, fixture, remaining=0
        )
    )
    assert blocked["calls"] == 0


def test_retrieval_quality_excludes_wrong_version_and_expired(database, monkeypatch):
    index_memory(database)
    monkeypatch.setenv("RETRIEVAL_MIN_SCORE", "0")
    with database.session() as session:
        session.execute(
            text(
                "UPDATE semantic_memory SET valid_until = now() - interval '1 day' "
                "WHERE source_id = 'solar'"
            )
        )
        session.execute(
            text(
                "UPDATE semantic_memory SET metadata = '{\"version\": 99}' "
                "WHERE source_id = 'reserve'"
            )
        )
    result = select_context(database, "synthetic", "solar-persistence-demo-v1")
    assert [item["source_id"] for item in result["selected"]] == ["units"]
    assert (
        next(item for item in result["candidates"] if item["source_id"] == "reserve")[
            "selection_reason"
        ]
        == "wrong configuration/version"
    )


def test_offline_model_continues_with_low_confidence(database, monkeypatch):
    monkeypatch.setenv("AGENT_BACKEND", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:1")
    result = asyncio.run(run_episode(database, "sunny", interpretation_enabled=True))
    publication = get_publication(database, result["publication_id"])
    assert publication["status"] == "valid"
    assert publication["profile"]["confidence"] == "low"
    assert publication["interpretation"]["accepted"] is False
