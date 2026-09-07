import asyncio
from uuid import UUID

from sqlalchemy import text

from pap_agent.store import get_episode
from pap_agent.workflow import run_episode


def test_checkpoint_resume_preserves_domain_ids(database):
    async def exercise():
        paused = await run_episode(database, "sunny", interrupt_after=["acquire_evidence"])
        episode_id = UUID(paused["episode_id"])
        assert get_episode(database, episode_id) is None
        resumed = await run_episode(database, episode_id=episode_id)
        completed = await run_episode(database, episode_id=episode_id)
        assert resumed == completed == get_episode(database, episode_id)
        assert resumed["evidence_id"] == paused["evidence_id"]
        assert resumed["status"] == "valid"
        assert [item["node"] for item in resumed["trace"]] == [
            "acquire_evidence (T1/T2/T3)",
            "calculate_profile (T4/T5/T6)",
            "publish_profile (T7)",
            "finalize_episode",
        ]

    asyncio.run(exercise())
    with database.session() as session:
        for table in (
            "evidence_records",
            "calculation_records",
            "episode_records",
            "pap_publications",
        ):
            assert session.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() == 1
        assert session.execute(text("SELECT count(*) FROM checkpoints")).scalar_one() > 0


def test_invalid_evidence_skips_calculation(database, source_database):
    with database.session() as session:
        session.execute(
            text("""UPDATE source_fixture.telemetry_snapshots
            SET timestamp = timestamp - interval '10 minutes'""")
        )
    result = asyncio.run(run_episode(database))
    assert result["status"] == "withheld"
    assert result["calculation_id"] == ""
    assert len(result["trace"]) == 3
