"""A paired measurement on one evidence snapshot, not a model-quality benchmark."""

from time import perf_counter

from pap_agent.database import Database
from pap_agent.evidence import acquire
from pap_agent.store import get_calculation, get_publication
from pap_agent.workflow import run_episode


async def compare_agents(database: Database, scenario="mysolark") -> dict:
    evidence = await acquire(database, scenario)
    runs = []
    intervals = []
    for enabled in (False, True):
        started = perf_counter()
        episode = await run_episode(
            database, scenario, evidence_id=evidence.id, interpretation_enabled=enabled
        )
        elapsed = round((perf_counter() - started) * 1000)
        calculation = (
            get_calculation(database, episode["calculation_id"])
            if (episode["calculation_id"])
            else None
        )
        intervals.append(
            calculation["pap"]["intervals"] if calculation and calculation["pap"] else None
        )
        publication = get_publication(database, episode["publication_id"])
        runs.append(
            {
                "interpretation_enabled": enabled,
                "elapsed_ms": elapsed,
                "model_calls": episode["model_calls"],
                "episode": episode,
                "confidence": publication["profile"]["confidence"]
                if publication["profile"]
                else None,
            }
        )
    return {
        "evidence_id": str(evidence.id),
        "runs": runs,
        "same_available_power": intervals[0] is not None and intervals[0] == intervals[1],
        "note": "One paired run, baseline first; warm-up and latency are not quality scores.",
    }
