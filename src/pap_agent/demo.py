"""Command-line evidence → PAP → feedback → paired-agent demo, using labeled synthetic input."""

import asyncio
import json
from datetime import timedelta
from uuid import UUID

from pap_agent.comparison import compare_agents
from pap_agent.config import Settings
from pap_agent.database import Database
from pap_agent.evidence import Evidence, validate_sources
from pap_agent.memory import index_memory
from pap_agent.outcomes import evaluate_publication
from pap_agent.runtime import readiness
from pap_agent.selection import RunSelection
from pap_agent.sources import telemetry_source, weather_source
from pap_agent.store import save_evidence
from pap_agent.workflow import run_episode


async def demo(database: Database) -> dict:
    ready = await readiness(database, Settings())
    if ready["status"] != "ready":
        return {"readiness": ready}
    index_memory(database)
    first = await run_episode(database, "sunny", interpretation_enabled=False)
    # Real T3 validation, with the fixture deliberately aged ten minutes.
    telemetry = telemetry_source("sunny")
    try:
        validate_sources(
            telemetry,
            weather_source(RunSelection(), telemetry.source_time, scenario="sunny"),
            telemetry.source_time + timedelta(minutes=10),
        )
    except ValueError:
        stale = Evidence(
            status="withheld", reason="Synthetic stale demo: T3 rejected aged telemetry"
        )
    else:
        raise AssertionError("Stale demo should fail T3")
    save_evidence(database, stale.model_dump(mode="json"))
    withheld = await run_episode(database, "sunny", evidence_id=stale.id)
    if first["status"] == "valid":
        await evaluate_publication(database, UUID(first["publication_id"]))
        index_memory(database)
    pair = await compare_agents(database, "sunny")
    return {
        "readiness": ready,
        "first": {key: first[key] for key in ("publication_id", "status", "reasoning_mode")},
        "stale": {"publication_id": withheld["publication_id"], "status": withheld["status"]},
        "same_available_power": pair["same_available_power"],
        "comparison": [
            {
                "publication_id": run["episode"]["publication_id"],
                "status": run["episode"]["status"],
                "calls": run["model_calls"],
                "elapsed_ms": run["elapsed_ms"],
                "interpretation_enabled": run["interpretation_enabled"],
            }
            for run in pair["runs"]
        ],
    }


if __name__ == "__main__":
    database = Database(Settings())
    try:
        result = asyncio.run(demo(database))
        print(json.dumps(result, indent=2))
        if result["readiness"]["status"] != "ready":
            raise SystemExit(1)
    finally:
        database.close()
