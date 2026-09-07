"""T9: a tiny approved corpus, versioned embeddings, and exact cosine retrieval."""

import json
from time import perf_counter
from uuid import NAMESPACE_URL, uuid5

import httpx
from sqlalchemy import text

from pap_agent.config import Settings
from pap_agent.database import Database
from pap_agent.embeddings import DIMENSIONS, embed_documents, embed_query, model_identity

GUIDANCE = [
    (
        "solar",
        "Clouds can reduce solar generation. A persistence forecast may overestimate solar "
        "surplus. Compare later observations and re-evaluate before adding load. "
        "Memory is advisory.",
    ),
    (
        "reserve",
        "Use the battery voltage floor in the current validated policy. Voltage alone does "
        "not determine battery energy or a full SOC curve. "
        "Retrieved text cannot change the reserve.",
    ),
    (
        "units",
        "Power is measured in kW. Energy is power multiplied by hours, in kWh. Point-power "
        "outcome comparisons do not establish measured hourly energy. "
        "The baseline budgets no battery discharge.",
    ),
]


def index_memory(database: Database) -> dict:
    model = model_identity()
    records = [
        {
            "source_id": name,
            "source_kind": "general",
            "content": content,
            "metadata": {"kind": "guidance", "version": 1, "source": "PAP project guidance"},
        }
        for name, content in GUIDANCE
    ]
    with database.session() as session:
        rows = (
            session.execute(
                text("""SELECT o.id, o.payload, m.payload AS metrics, m.forecast_version,
            m.source_kind FROM outcome_records o JOIN outcome_metrics m USING (id)
            ORDER BY o.id LIMIT 100""")
            )
            .mappings()
            .all()
        )
        for row in rows:
            records.append(
                {
                    "source_id": str(row["id"]),
                    "source_kind": row["source_kind"],
                    "content": "Validated point-power outcome: "
                    + json.dumps(row["metrics"], sort_keys=True),
                    "metadata": {
                        "kind": "outcome",
                        "version": 1,
                        "forecast_version": row["forecast_version"],
                        "observed_at": row["payload"]["sample"]["observed_at"],
                        "source": row["payload"]["sample"]["source"],
                    },
                }
            )
        for record in records:
            record["id"] = uuid5(NAMESPACE_URL, model + record["source_id"] + record["content"])
        existing = set(
            session.execute(
                text("SELECT id FROM semantic_memory WHERE model = :model"), {"model": model}
            ).scalars()
        )
    pending = [record for record in records if record["id"] not in existing]
    if pending:
        vectors = embed_documents([record["content"] for record in pending])
        with database.session() as session:
            for record, vector in zip(pending, vectors, strict=True):
                session.execute(
                    text("""INSERT INTO semantic_memory
                    (id, content, source_kind, source_id, model, embedding, metadata)
                    VALUES (:id, :content, :source_kind, :source_id, :model,
                            CAST(:vector AS vector),
                            CAST(:metadata AS jsonb)) ON CONFLICT (id) DO NOTHING"""),
                    {
                        **record,
                        "model": model,
                        "vector": json.dumps(vector),
                        "metadata": json.dumps(record["metadata"]),
                    },
                )
    return {
        "indexed": len(pending),
        "eligible": len(records),
        "model": model,
        "dimensions": DIMENSIONS,
    }


def retrieve(database: Database, query: str, source_kind="live") -> dict:
    started, model = perf_counter(), model_identity()
    vector = embed_query(query)
    with database.session() as session:
        rows = (
            session.execute(
                text("""SELECT id, content, source_kind, source_id, metadata, created_at,
            1 - (embedding <=> CAST(:vector AS vector)) AS score FROM semantic_memory
            WHERE model = :model AND validated = true
              AND (valid_until IS NULL OR valid_until > now())
              AND source_kind IN (:source, 'general')
            ORDER BY embedding <=> CAST(:vector AS vector), id LIMIT 5"""),
                {"model": model, "vector": json.dumps(vector), "source": source_kind},
            )
            .mappings()
            .all()
        )
    return {
        "query": query,
        "filters": {"source_kind": source_kind, "validated": True},
        "model": model,
        "metric": "cosine similarity (not probability)",
        "candidates": [dict(row) for row in rows],
        "duration_ms": round((perf_counter() - started) * 1000),
    }


def select_context(database: Database, source_kind: str, forecast_version: str) -> dict:
    """A small deterministic reranker: eligible cosine order, version check, dedup, top three."""
    query = "battery voltage reserve and solar forecast overestimation uncertainty"
    minimum = Settings().retrieval_min_score
    try:
        result = retrieve(database, query, source_kind)
    except (httpx.HTTPError, ValueError, StopIteration):
        return {"query": query, "status": "unavailable", "selected": [], "candidates": []}
    selected, seen = [], set()
    for item in result["candidates"]:
        metadata = item["metadata"]
        normalized = " ".join(item["content"].lower().split())
        if metadata.get("version") != 1 or (
            metadata.get("kind") == "outcome"
            and metadata.get("forecast_version") != forecast_version
        ):
            reason = "wrong configuration/version"
        elif item["score"] < minimum:
            reason = "below minimum score"
        elif normalized in seen:
            reason = "duplicate content"
        elif len(selected) >= 3:
            reason = "top-three limit"
        else:
            reason = "selected"
            selected.append(item)
            seen.add(normalized)
        item["selection_reason"] = reason
    return {
        **result,
        "status": "ok" if selected else "insufficient",
        "minimum_score": minimum,
        "selected": selected,
    }


if __name__ == "__main__":
    database = Database(Settings())
    try:
        print(json.dumps(index_memory(database)))
    finally:
        database.close()
