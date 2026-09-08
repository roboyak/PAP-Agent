"""T8 compares point power samples, not completed-hour energy or calibrated probabilities."""

import json
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4, uuid5

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from langsmith import tracing_context
from sqlalchemy import text
from typing_extensions import TypedDict

from pap_agent.calibration import calibration
from pap_agent.database import Database
from pap_agent.domain import ForecastInterval, TelemetrySnapshot
from pap_agent.evidence import acquire, validate_telemetry
from pap_agent.selection import RunSelection
from pap_agent.sources import SourceResult
from pap_agent.store import get_calculation, get_publication


class EvaluationState(TypedDict):
    publication_id: str
    outcome_id: str


def evaluate_sample(database: Database, publication: dict, sample: TelemetrySnapshot) -> dict:
    selection = RunSelection.model_validate(publication.get("selection", {}))
    if selection.replay_at:
        raise ValueError("Historical snapshot replay does not update live outcome feedback")
    expected = publication["evidence"]["telemetry"]
    if sample.data_mode != expected["data_mode"] or (
        sample.data_mode == "live" and sample.source != expected["source"]
    ):
        raise ValueError("Outcome must come from the same wing and source")
    calculation = get_calculation(database, publication["calculation_id"])
    forecasts = [ForecastInterval.model_validate(item) for item in calculation["forecast"]]
    index = next(
        (
            i
            for i, item in enumerate(forecasts)
            if item.starts_at <= sample.observed_at < item.ends_at
        ),
        None,
    )
    if index is None:
        raise ValueError("Observation is outside this profile's forecast horizon")
    predicted = forecasts[index]
    floor = publication["evidence"]["policy"]["min_battery_voltage_v"]
    actual_extra = max(0, sample.solar_power_kw - sample.load_power_kw)
    if sample.battery_voltage_v <= floor:
        actual_extra = 0
    cap = publication["evidence"]["policy"]["max_extra_power_kw"]
    if cap is not None:
        actual_extra = min(actual_extra, cap)
    metrics = {
        "kind": "point_power_sample",
        "interval_index": index,
        "solar_bias_kw": predicted.generation_kw - sample.solar_power_kw,
        "load_error_kw": abs(predicted.demand_kw - sample.load_power_kw),
        "availability_error_kw": abs(
            publication["profile"]["intervals"][index]["available_kw"] - actual_extra
        ),
    }
    record_id = uuid5(UUID(publication["id"]), str(sample.id))
    raw = {
        "id": str(record_id),
        "publication_id": publication["id"],
        "sample": sample.model_dump(mode="json"),
    }
    version, source = calculation["forecast_version"], selection.feedback_scope(sample.data_mode)
    with database.session() as session:
        session.execute(
            text("""INSERT INTO outcome_records VALUES (:id, :publication, CAST(:payload AS jsonb))
            ON CONFLICT (id) DO NOTHING"""),
            {"id": record_id, "publication": publication["id"], "payload": json.dumps(raw)},
        )
        session.execute(
            text("""INSERT INTO outcome_metrics
            VALUES (:id, :source, :version, :bias, CAST(:payload AS jsonb))
            ON CONFLICT (id) DO NOTHING"""),
            {
                "id": record_id,
                "source": source,
                "version": version,
                "bias": metrics["solar_bias_kw"],
                "payload": json.dumps(metrics),
            },
        )
    summary = calibration(database, source, version)
    with database.session() as session:
        session.execute(
            text("""INSERT INTO calibration_records
            VALUES (:source, :version, CAST(:payload AS jsonb))
            ON CONFLICT (source_kind, forecast_version)
            DO UPDATE SET payload = excluded.payload"""),
            {"source": source, "version": version, "payload": json.dumps(summary)},
        )
    return {"outcome": raw, "metrics": metrics, "calibration": summary}


async def evaluate_publication(database: Database, publication_id: UUID) -> dict:
    publication = get_publication(database, publication_id)
    if publication is None or publication["status"] != "valid":
        raise ValueError("A validated publication is required")
    selection = RunSelection.model_validate(publication.get("selection", {}))
    if selection.replay_at:
        raise ValueError("Historical snapshot replay does not update live outcome feedback")

    async def observe_and_evaluate(state: EvaluationState):
        source = publication["evidence"]["telemetry"]["data_mode"]
        if source == "synthetic":
            # Explicit cloudy demo, kept separate from real-world feedback.
            sample = TelemetrySnapshot.model_validate(publication["evidence"]["telemetry"])
            sample.id = uuid5(publication_id, "cloudy-demo")
            sample.observed_at += timedelta(minutes=30)
            sample.solar_power_kw *= 0.5
            sample.source = "Synthetic cloudy outcome"
        else:
            evidence = await acquire(database, "mysolark", selection=selection)
            # T8 measures telemetry, even if T3 withheld a new weather forecast.
            # Reuse the recorded MCP call and apply the same telemetry checks.
            telemetry = next(
                (
                    call["result"]
                    for call in evidence.calls
                    if call["tool"] == "get_current_telemetry"
                ),
                None,
            )
            if telemetry is None:
                raise ValueError("No fresh observed outcome is available")
            sample = validate_telemetry(
                SourceResult.model_validate(telemetry), datetime.now(UTC), selection
            )
            if sample.observed_at <= datetime.fromisoformat(
                publication["evidence"]["telemetry"]["observed_at"]
            ):
                raise ValueError("No newer MySolArk scrape yet; evaluate after the next scrape")
        result = evaluate_sample(database, publication, sample)
        return {"outcome_id": result["outcome"]["id"]}

    graph = StateGraph(EvaluationState)
    graph.add_node("observe_and_evaluate", observe_and_evaluate)
    graph.add_edge(START, "observe_and_evaluate")
    graph.add_edge("observe_and_evaluate", END)
    dsn = database.engine.url.set(drivername="postgresql").render_as_string(hide_password=False)
    async with AsyncPostgresSaver.from_conn_string(dsn) as saver:
        await saver.setup()
        with tracing_context(enabled=False):
            result = await graph.compile(checkpointer=saver).ainvoke(
                {"publication_id": str(publication_id), "outcome_id": ""},
                {"configurable": {"thread_id": f"evaluation-{uuid4()}"}, "recursion_limit": 3},
            )
    with database.session() as session:
        row = (
            session.execute(
                text("""SELECT o.payload AS outcome, m.payload AS metrics
            FROM outcome_records o JOIN outcome_metrics m USING (id) WHERE o.id = :id"""),
                {"id": result["outcome_id"]},
            )
            .mappings()
            .one()
        )
    calculation = get_calculation(database, publication["calculation_id"])
    return {
        **row,
        "calibration": calibration(
            database,
            selection.feedback_scope(row["outcome"]["sample"]["data_mode"]),
            calculation["forecast_version"],
        ),
    }
