import asyncio
from uuid import UUID

from pap_agent.outcomes import evaluate_publication
from pap_agent.store import get_publication
from pap_agent.workflow import run_episode


def test_feedback_changes_confidence_only_and_deduplicates(database):
    async def exercise():
        episode = await run_episode(database, "sunny")
        publication = get_publication(database, UUID(episode["publication_id"]))
        outcome = await evaluate_publication(database, UUID(publication["id"]))
        assert outcome["metrics"]["solar_bias_kw"] == 2
        assert outcome["calibration"]["samples"] == 1
        repeated = await evaluate_publication(database, UUID(publication["id"]))
        assert repeated["calibration"]["samples"] == 1
        next_episode = await run_episode(database, "sunny")
        later = get_publication(database, UUID(next_episode["publication_id"]))
        assert publication["profile"]["confidence"] == "reduced"
        assert later["profile"]["confidence"] == "low"
        assert later["profile"]["intervals"] == publication["profile"]["intervals"]
        assert later["evidence"]["policy"] == publication["evidence"]["policy"]

    asyncio.run(exercise())
