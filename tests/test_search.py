import asyncio
from collections import Counter
from uuid import UUID, uuid4

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from pap_agent import search
from pap_agent.outcomes import evaluate_publication
from pap_agent.reasoning import get_record
from pap_agent.store import get_publication
from pap_agent.workflow import checkpoint_dsn, run_episode


async def seed_ambiguity(database):
    normal = await run_episode(database, "sunny")
    assert normal["reasoning_mode"] == "linear" and "search_id" not in normal
    await evaluate_publication(database, UUID(normal["publication_id"]))
    return normal


def test_grounded_search_recovers_after_hard_pruning(database, monkeypatch):
    generate, score = search.generate_candidates, search.score_candidates

    async def candidates(*args):
        result = await generate(*args)
        result["candidates"][0]["evidence_ids"] = ["invented"]
        return result

    async def critic(db, state, context, branches):
        assert all("invented" not in item["candidate"]["evidence_ids"] for item in branches)
        return await score(db, state, context, branches)

    monkeypatch.setattr(search, "generate_candidates", candidates)
    monkeypatch.setattr(search, "score_candidates", critic)
    normal = asyncio.run(seed_ambiguity(database))
    result = asyncio.run(run_episode(database, "sunny"))
    record = get_record(database, result["search_id"])
    assert result["reasoning_mode"] == "selective_tot"
    assert record["status"] == "valid" and len(record["branches"]) == 3
    assert record["branches"][0]["prune_reason"] == "Unsupported evidence citation"
    assert record["guidance"]["fallback"] == "refresh_telemetry"
    assert record["submission"] == {"depth": 3, "hard_errors": []}
    assert (
        get_publication(database, result["publication_id"])["profile"]["intervals"]
        == (get_publication(database, normal["publication_id"])["profile"]["intervals"])
    )


def test_search_one_revision_bounds_and_checkpoint_resume(database, monkeypatch):
    async def close_scores(db, state, context, branches):
        return {
            "scores": {
                item["id"]: {
                    "grounding": 20,
                    "freshness": 15,
                    "consistency": 15,
                    "uncertainty": 15,
                    "usefulness": 10,
                }
                for item in branches
            },
            "calls": 0,
            "agent_ids": [],
        }

    monkeypatch.setattr(search, "score_candidates", close_scores)

    async def exercise():
        await seed_ambiguity(database)
        paused = await run_episode(database, "sunny", interrupt_after=["retrieve"])
        config = {"configurable": {"thread_id": f"search-test-{uuid4()}"}, "recursion_limit": 24}
        async with AsyncPostgresSaver.from_conn_string(checkpoint_dsn(database)) as saver:
            await saver.setup()
            initial = await search.build_search(database, saver, ["generate"]).ainvoke(
                paused, config
            )
            first_ids = {
                item["id"] for item in get_record(database, initial["search_id"])["branches"]
            }
            completed = await search.build_search(database, saver).ainvoke(None, config)
        record = get_record(database, completed["search_id"])
        assert len(record["branches"]) == len({item["id"] for item in record["branches"]}) == 9
        assert first_ids <= {item["id"] for item in record["branches"]}
        assert max(Counter(item["parent_id"] for item in record["branches"]).values()) == 3
        assert len(record["beams"]) == 2 and all(len(beam) <= 2 for beam in record["beams"])
        assert max(item["depth"] for item in record["branches"]) == 2
        assert record["submission"]["depth"] == 3 and record["model_calls"] <= 8
        assert record["stop_reason"] == "One-revision/depth limit"

    asyncio.run(exercise())


def test_no_acceptable_branch_withholds(database, monkeypatch):
    generate = search.generate_candidates

    async def unsupported(*args):
        result = await generate(*args)
        for candidate in result["candidates"]:
            candidate["unsupported_assumptions"] = ["Invent battery energy"]
        return result

    monkeypatch.setattr(search, "generate_candidates", unsupported)
    asyncio.run(seed_ambiguity(database))
    result = asyncio.run(run_episode(database, "sunny"))
    assert result["status"] == "withheld"
    assert get_publication(database, result["publication_id"])["profile"] is None
