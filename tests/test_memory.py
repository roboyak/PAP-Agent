from sqlalchemy import text

from pap_agent.memory import index_memory, retrieve


def test_vector_round_trip_and_eligible_retrieval(database):
    assert index_memory(database)["indexed"] == 3
    assert index_memory(database)["indexed"] == 0
    result = retrieve(database, "battery voltage reserve")
    assert result["model"] == "test-hash-v1"
    assert result["candidates"][0]["source_id"] == "reserve"
    assert 0 < result["candidates"][0]["score"] <= 1
    with database.session() as session:
        assert (
            session.execute(
                text("SELECT vector_dims(embedding) FROM semantic_memory LIMIT 1")
            ).scalar_one()
            == 768
        )
        session.execute(
            text("UPDATE semantic_memory SET validated = false WHERE source_id = 'reserve'")
        )
    assert all(
        row["source_id"] != "reserve"
        for row in retrieve(database, "battery voltage reserve")["candidates"]
    )
