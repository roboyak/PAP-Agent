"""Small durable control flow. Domain facts live in their own PostgreSQL records."""

from time import perf_counter
from typing import Literal
from uuid import UUID, uuid4, uuid5

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, START, StateGraph
from langsmith import tracing_context
from typing_extensions import TypedDict

from pap_agent.core import Calculation, calculate
from pap_agent.database import Database
from pap_agent.evidence import Evidence, acquire
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
    status: Literal["running", "valid", "withheld"]
    stop_reason: str
    trace: list[dict]


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
        record_id = uuid5(UUID(state["episode_id"]), "evidence")
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

    graph = StateGraph(PAPGraphState)
    graph.add_node("acquire_evidence", acquire_evidence)
    graph.add_node("calculate_profile", calculate_profile)
    graph.add_node("finalize_episode", finalize_episode)
    graph.add_edge(START, "acquire_evidence")
    graph.add_conditional_edges(
        "acquire_evidence",
        lambda state: state["status"],
        {"valid": "calculate_profile", "withheld": "finalize_episode"},
    )
    graph.add_edge("calculate_profile", "finalize_episode")
    graph.add_edge("finalize_episode", END)
    return graph.compile(checkpointer=checkpointer, interrupt_after=interrupt_after)


async def run_episode(
    database: Database, scenario="mysolark", episode_id: UUID | None = None, interrupt_after=None
) -> PAPGraphState:
    episode_id = episode_id or uuid4()
    config = {"configurable": {"thread_id": str(episode_id)}, "recursion_limit": 8}
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
                "evidence_id": "",
                "calculation_id": "",
                "status": "running",
                "stop_reason": "",
                "trace": [],
            }
        )
        with tracing_context(enabled=False):
            return await graph.ainvoke(initial, config)
