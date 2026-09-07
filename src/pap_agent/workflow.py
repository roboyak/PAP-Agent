"""Small durable control flow. Domain facts live in their own PostgreSQL records."""

import json
import logging
from time import perf_counter
from typing import Literal, NotRequired
from uuid import UUID, uuid4, uuid5

from fastapi.encoders import jsonable_encoder
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from langsmith import tracing_context
from typing_extensions import TypedDict

from pap_agent.agents import Advice, call_agent, validated_advice
from pap_agent.config import Settings
from pap_agent.core import Calculation, calculate
from pap_agent.database import Database
from pap_agent.evidence import Evidence, acquire
from pap_agent.memory import select_context
from pap_agent.publisher import publish
from pap_agent.reasoning import get_record, save_record
from pap_agent.store import (
    get_calculation,
    get_episode,
    get_evidence,
    save_calculation,
    save_episode,
)


class PAPGraphState(TypedDict):
    episode_id: str
    scenario: str
    evidence_id: str
    calculation_id: str
    publication_id: NotRequired[str]
    status: Literal["running", "valid", "withheld"]
    stop_reason: str
    trace: list[dict]
    interpretation_enabled: NotRequired[bool]
    retrieval_id: NotRequired[str]
    interpretation_id: NotRequired[str]
    advice_accepted: NotRequired[bool]
    model_calls: NotRequired[int]


def checkpoint_dsn(database: Database) -> str:
    return database.engine.url.set(drivername="postgresql").render_as_string(hide_password=False)


def build_graph(database: Database, checkpointer, interrupt_after=None):
    def event(state, node, status, started, record_id=""):
        return [
            *state["trace"],
            {
                "node": node,
                "status": status,
                "record_id": record_id,
                "duration_ms": round((perf_counter() - started) * 1000),
            },
        ]

    async def acquire_evidence(state: PAPGraphState):
        started = perf_counter()
        record_id = state["evidence_id"] or uuid5(UUID(state["episode_id"]), "evidence")
        stored = get_evidence(database, record_id)
        evidence = (
            Evidence.model_validate(stored)
            if stored
            else await acquire(database, state["scenario"], record_id)
        )
        return {
            "evidence_id": str(evidence.id),
            "status": evidence.status,
            "stop_reason": evidence.reason,
            "trace": event(
                state, "acquire_evidence (T1/T2/T3)", evidence.status, started, str(evidence.id)
            ),
        }

    def calculate_profile(state: PAPGraphState):
        started = perf_counter()
        record_id = uuid5(UUID(state["episode_id"]), "calculation")
        stored = get_calculation(database, record_id)
        if stored is None:
            result = calculate(
                Evidence.model_validate(get_evidence(database, state["evidence_id"])), record_id
            )
            save_calculation(database, result.model_dump(mode="json"))
        result = Calculation.model_validate(get_calculation(database, record_id))
        return {
            "calculation_id": str(result.id),
            "status": result.status,
            "stop_reason": "; ".join(result.validation) or "T6 passed",
            "trace": event(
                state, "calculate_profile (T4/T5/T6)", result.status, started, str(result.id)
            ),
        }

    def finalize_episode(state: PAPGraphState):
        trace = event(state, "finalize_episode", state["status"], perf_counter())
        save_episode(database, {**state, "trace": trace})
        return {"trace": trace}

    def retrieve_context(state: PAPGraphState):
        started = perf_counter()
        record_id = uuid5(UUID(state["episode_id"]), "retrieval")
        record = get_record(database, record_id)
        if record is None:
            evidence = Evidence.model_validate(get_evidence(database, state["evidence_id"]))
            calculation = get_calculation(database, state["calculation_id"])
            record = jsonable_encoder(
                {
                    "id": str(record_id),
                    "episode_id": state["episode_id"],
                    "kind": "retrieval",
                    **select_context(
                        database,
                        evidence.scenario.telemetry.data_mode,
                        calculation["forecast_version"],
                    ),
                }
            )
            save_record(database, record)
        return {
            "retrieval_id": str(record_id),
            "trace": event(state, "retrieve (T9)", record["status"], started, str(record_id)),
        }

    async def grounded_interpretation(state: PAPGraphState):
        started = perf_counter()
        record_id = uuid5(UUID(state["episode_id"]), "interpretation")
        evidence = Evidence.model_validate(get_evidence(database, state["evidence_id"]))
        selected = get_record(database, state["retrieval_id"])["selected"]
        context = {
            "task": "Interpret reserve and solar uncertainty; recommend keep/lower confidence "
            "and none/refresh_telemetry fallback. Explain uncertainty in one short sentence "
            "under 180 characters, with no numbers. "
            "Do not restate battery position or memory count in the explanation. "
            "Cite only the IDs below. Set insufficient true only if these inputs cannot "
            "support an advisory recommendation.",
            "evidence_id": state["evidence_id"],
            "telemetry": evidence.scenario.telemetry.model_dump(mode="json"),
            "policy": evidence.scenario.policy.model_dump(mode="json"),
            "forecast": "12-hour solar persistence with synthetic weather; battery budget 0 kWh",
            "validated_facts": {
                "battery_above_floor": evidence.scenario.telemetry.battery_voltage_v
                > evidence.scenario.policy.min_battery_voltage_v,
                "selected_memory_count": len(selected),
                "hard_checks": "T3 and T6 passed; never override them",
            },
            "memory": selected,
        }
        fixture = {
            "evidence_ids": [state["evidence_id"], *[str(i["id"]) for i in selected]],
            "confidence": "lower",
            "fallback": "refresh_telemetry",
            "re_evaluate": True,
            "explanation": "Re-evaluate solar uncertainty before adding optional load.",
            "insufficient": not bool(selected),
        }
        record = await call_agent(
            database, record_id, state["episode_id"], "interpretation", context, Advice, fixture
        )
        return {
            "interpretation_id": str(record_id),
            "model_calls": record["calls"],
            "trace": event(
                state, "grounded_interpretation", record["status"], started, str(record_id)
            ),
        }

    def validate_recommendation(state: PAPGraphState):
        record = get_record(database, state["interpretation_id"])
        selected = get_record(database, state["retrieval_id"])["selected"]
        accepted = validated_advice(record, state["evidence_id"], selected) is not None
        return {
            "advice_accepted": accepted,
            "trace": event(
                state,
                "validate_recommendation",
                "accepted" if accepted else "rejected",
                perf_counter(),
                state["interpretation_id"],
            ),
        }

    def publish_profile(state: PAPGraphState):
        started = perf_counter()
        publication = publish(
            database,
            UUID(state["episode_id"]),
            UUID(state["evidence_id"]),
            UUID(state["calculation_id"]) if state["calculation_id"] else None,
            interpretation_id=state.get("interpretation_id"),
            retrieval_id=state.get("retrieval_id"),
        )
        logging.getLogger("uvicorn.error").info(
            json.dumps(
                {
                    "episode_id": state["episode_id"],
                    "node": "publish_profile",
                    "pap_id": str(publication.id),
                    "evidence_id": state["evidence_id"],
                    "status": publication.status,
                    "reason": publication.reason,
                }
            )
        )
        return {
            "publication_id": str(publication.id),
            "status": publication.status,
            "stop_reason": publication.reason,
            "trace": event(
                state, "publish_profile (T7)", publication.status, started, str(publication.id)
            ),
        }

    graph = StateGraph(PAPGraphState)
    graph.add_node("acquire_evidence", acquire_evidence)
    graph.add_node("calculate_profile", calculate_profile)
    graph.add_node("finalize_episode", finalize_episode)
    graph.add_node("publish_profile", publish_profile)
    graph.add_node("retrieve", retrieve_context)
    graph.add_node("grounded_interpretation", grounded_interpretation)
    graph.add_node("validate_recommendation", validate_recommendation)
    graph.add_edge(START, "acquire_evidence")
    graph.add_conditional_edges(
        "acquire_evidence",
        lambda state: state["status"],
        {"valid": "calculate_profile", "withheld": "publish_profile"},
    )
    graph.add_conditional_edges(
        "calculate_profile",
        lambda state: (
            "retrieve"
            if state["status"] == "valid" and state.get("interpretation_enabled")
            else "publish_profile"
        ),
        ["retrieve", "publish_profile"],
    )
    graph.add_edge("retrieve", "grounded_interpretation")
    graph.add_edge("grounded_interpretation", "validate_recommendation")
    graph.add_edge("validate_recommendation", "publish_profile")
    graph.add_edge("publish_profile", "finalize_episode")
    graph.add_edge("finalize_episode", END)
    return graph.compile(checkpointer=checkpointer, interrupt_after=interrupt_after)


async def run_episode(
    database: Database,
    scenario="mysolark",
    episode_id: UUID | None = None,
    interrupt_after=None,
    *,
    evidence_id=None,
    interpretation_enabled: bool | None = None,
) -> PAPGraphState:
    episode_id = episode_id or uuid4()
    config = {"configurable": {"thread_id": str(episode_id)}, "recursion_limit": 12}
    async with AsyncPostgresSaver.from_conn_string(checkpoint_dsn(database)) as saver:
        await saver.setup()
        graph = build_graph(database, saver, interrupt_after)
        previous = await graph.aget_state(config)
        if previous.values and not previous.next:
            return get_episode(database, episode_id)
        initial = (
            None
            if previous.values
            else {
                "episode_id": str(episode_id),
                "scenario": scenario,
                "evidence_id": str(evidence_id) if evidence_id else "",
                "interpretation_enabled": Settings().enable_interpretation_agent
                if interpretation_enabled is None
                else interpretation_enabled,
                "model_calls": 0,
                "calculation_id": "",
                "status": "running",
                "stop_reason": "",
                "trace": [],
            }
        )
        with tracing_context(enabled=False):
            return await graph.ainvoke(initial, config)
