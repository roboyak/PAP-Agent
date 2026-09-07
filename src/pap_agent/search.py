"""Selective, bounded search over advisory fallbacks; numerical PAP never branches."""

from collections import Counter
from typing import Literal, NotRequired
from uuid import UUID, uuid5

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import TypedDict

from pap_agent.agents import MAX_MODEL_CALLS, call_agent
from pap_agent.core import calculate
from pap_agent.evidence import Evidence
from pap_agent.reasoning import get_record, model_call_count, save_record
from pap_agent.store import get_evidence

LIMITS = {
    "branch_factor": 3,
    "beam_width": 2,
    "max_depth": 3,
    "max_revisions": 1,
    "max_model_calls": MAX_MODEL_CALLS,
}


class Thought(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence_ids: list[str] = Field(min_length=1, max_length=5)
    fallback: Literal["baseline", "refresh_telemetry", "withhold"]
    uncertainty: Literal["baseline", "elevated"]
    summary: str = Field(min_length=1, max_length=240)
    unsupported_assumptions: list[str] = Field(default_factory=list, max_length=2)


class Candidate(Thought):
    parent_id: str


class GeneratedThoughts(BaseModel):
    model_config = ConfigDict(extra="forbid")
    thoughts: list[Thought] = Field(min_length=1, max_length=3)


class Rubric(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grounding: int = Field(ge=0, le=25)
    freshness: int = Field(ge=0, le=20)
    consistency: int = Field(ge=0, le=20)
    uncertainty: int = Field(ge=0, le=20)
    usefulness: int = Field(ge=0, le=15)


class ScoredThought(BaseModel):
    model_config = ConfigDict(extra="forbid")
    branch_id: str
    rubric: Rubric


class Critique(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scores: list[ScoredThought] = Field(min_length=1, max_length=6)


class SearchState(TypedDict):
    episode_id: str
    evidence_id: str
    calculation_id: str
    assessment_id: str
    retrieval_id: str
    model_calls: int
    trace: list[dict]
    search_id: NotRequired[str]
    search_round: NotRequired[int]
    search_done: NotRequired[bool]


async def generate_candidates(database, state, context, parents):
    """One isolated generator invocation per parent; Python supplies the parent IDs."""
    candidates, agent_ids, calls = [], [], 0
    for parent in parents:
        fixture = []
        for fallback, summary in (
            ("baseline", "Keep the persistence evaluation with its stated assumptions."),
            (
                "refresh_telemetry",
                "Observed overestimation supports refreshing before optional load.",
            ),
            ("withhold", "Withhold guidance until the forecast uncertainty is resolved."),
        ):
            fixture.append(
                Thought(
                    evidence_ids=context["evidence_ids"],
                    fallback=fallback,
                    uncertainty="elevated",
                    summary=summary,
                ).model_dump()
            )
        history = get_record(database, state.get("search_id")) if state.get("search_id") else None
        previous = (
            next(
                (branch["candidate"] for branch in history["branches"] if branch["id"] == parent),
                None,
            )
            if history
            else None
        )
        record = await call_agent(
            database,
            uuid5(UUID(parent), "generator"),
            state["episode_id"],
            "generator",
            {
                "task": "Propose up to three distinct advisory interpretations: baseline, "
                "refresh_telemetry, withhold. Use only supplied evidence_ids. "
                "Keep each summary under 100 characters. No new assumptions or arithmetic.",
                "evidence": context,
                "previous_summary": previous,
            },
            GeneratedThoughts,
            {"thoughts": fixture},
        )
        agent_ids.append(record["id"])
        calls += record["calls"]
        if record["status"] == "ok":
            candidates.extend(
                {**thought, "parent_id": parent} for thought in record["output"]["thoughts"]
            )
    return {"candidates": candidates, "calls": calls, "agent_ids": agent_ids}


async def score_candidates(database, state, context, branches):
    """A rubric score is a ranking aid, never probability or hard-check authority."""
    scores = []
    for branch in branches:
        values = {
            "refresh_telemetry": (23, 18, 18, 19, 13),
            "baseline": (20, 18, 16, 8, 9),
            "withhold": (20, 18, 17, 17, 9),
        }[branch["candidate"]["fallback"]]
        scores.append(
            {
                "branch_id": branch["id"],
                "rubric": dict(zip(Rubric.model_fields, values, strict=True)),
            }
        )
    record = await call_agent(
        database,
        uuid5(UUID(state["search_id"]), f"critic:{state['search_round']}"),
        state["episode_id"],
        "critic",
        {
            "task": "Score each surviving branch. Rubric maxima: grounding 25, freshness 20, "
            "consistency 20, uncertainty 20, usefulness 15. Scores rank guidance, "
            "not physical safety or probabilities. Favor an evidence-supported refresh "
            "over ignoring observed overestimation; withhold only if guidance is unusable.",
            "evidence": context,
            "survivors": [
                {key: branch[key] for key in ("id", "candidate", "hard_checks")}
                for branch in branches
            ],
        },
        Critique,
        {"scores": scores},
    )
    output = record["output"]["scores"] if record["status"] == "ok" else []
    allowed = {branch["id"] for branch in branches}
    known = all(item["branch_id"] in allowed for item in output)
    unique = len({item["branch_id"] for item in output}) == len(output)
    return {
        "scores": {item["branch_id"]: item["rubric"] for item in output}
        if known and unique
        else {},
        "calls": record["calls"],
        "agent_ids": [record["id"]],
    }


def hard_errors(database, state, candidate: Candidate, allowed: set[str]) -> list[str]:
    evidence = Evidence.model_validate(get_evidence(database, state["evidence_id"]))
    errors = calculate(evidence).validation
    if not set(candidate.evidence_ids) <= allowed:
        errors.append("Unsupported evidence citation")
    if candidate.unsupported_assumptions:
        errors.append("Unsupported critical assumption")
    return errors


def ranked(branches: list[dict]) -> list[dict]:
    ordered = sorted(branches, key=lambda item: (-item["score"], item["id"]))
    # Within five points, prefer stronger grounding and explicit uncertainty handling.
    if ordered:
        close = [item for item in ordered if ordered[0]["score"] - item["score"] <= 5]
        winner = max(
            close,
            key=lambda item: (
                item["rubric"]["grounding"],
                item["rubric"]["uncertainty"],
                item["score"],
            ),
        )
        ordered.remove(winner)
        ordered.insert(0, winner)
    return ordered


def build_search(database, checkpointer=None, interrupt_after=None):
    def load(state):
        return get_record(database, state["search_id"])

    async def generate(state: SearchState):
        search_id = str(uuid5(UUID(state["episode_id"]), "search"))
        record = get_record(database, search_id)
        if record is None:
            selected = get_record(database, state["retrieval_id"])["selected"]
            evidence = Evidence.model_validate(get_evidence(database, state["evidence_id"]))
            record = {
                "id": search_id,
                "episode_id": state["episode_id"],
                "kind": "search",
                "mode": "selective_tot",
                "limits": LIMITS,
                "branches": [],
                "beams": [],
                "agent_ids": [],
                "model_calls": state["model_calls"],
                "round": 1,
                "context": {
                    "evidence_ids": [state["evidence_id"], state["assessment_id"]],
                    "assessment": get_record(database, state["assessment_id"]),
                    "memory": selected,
                    "validated_state": {
                        "observed_at": evidence.scenario.telemetry.observed_at.isoformat(),
                        "battery_voltage_v": evidence.scenario.telemetry.battery_voltage_v,
                        "voltage_floor_v": evidence.scenario.policy.min_battery_voltage_v,
                        "forecast": "Solar persistence; synthetic weather; no battery discharge",
                        "checks": "T3 and T6 passed; power arithmetic cannot be changed",
                    },
                },
            }
        depth = record["round"]
        parents = record["beams"][-1] if record["beams"] else [search_id]
        if not any(branch["depth"] == depth for branch in record["branches"]):
            generated = await generate_candidates(database, state, record["context"], parents)
            record["model_calls"] = model_call_count(database, state["episode_id"])
            record["agent_ids"] = list(
                dict.fromkeys([*record["agent_ids"], *generated["agent_ids"]])
            )
            counts = Counter()
            for raw in generated["candidates"]:
                candidate = Candidate.model_validate(raw)
                parent = candidate.parent_id
                if parent not in parents or counts[parent] >= LIMITS["branch_factor"]:
                    continue
                index = counts[parent]
                counts[parent] += 1
                record["branches"].append(
                    {
                        "id": str(uuid5(UUID(search_id), f"{depth}:{parent}:{index}")),
                        "parent_id": parent,
                        "depth": depth,
                        "candidate": candidate.model_dump(),
                        "status": "proposed",
                        "hard_checks": [],
                        "prune_reason": None,
                        "score": None,
                    }
                )
        save_record(database, record, finish=True)
        return {"search_id": search_id, "search_round": depth, "model_calls": record["model_calls"]}

    def prune(state: SearchState):
        record = load(state)
        allowed = {
            *record["context"]["evidence_ids"],
            *(str(item["id"]) for item in record["context"]["memory"]),
        }
        for branch in record["branches"]:
            if branch["depth"] != state["search_round"]:
                continue
            errors = hard_errors(
                database, state, Candidate.model_validate(branch["candidate"]), allowed
            )
            branch.update(
                status="pruned" if errors else "survivor",
                hard_checks=errors or ["T3/T6 and evidence checks passed"],
                prune_reason="; ".join(errors) if errors else None,
            )
        save_record(database, record, finish=True)
        return {}

    async def critique(state: SearchState):
        record = load(state)
        survivors = [
            branch
            for branch in record["branches"]
            if branch["depth"] == state["search_round"] and branch["status"] == "survivor"
        ]
        scored = (
            await score_candidates(database, state, record["context"], survivors)
            if survivors
            else {"scores": {}, "calls": 0, "agent_ids": []}
        )
        record["model_calls"] = model_call_count(database, state["episode_id"])
        record["agent_ids"] = list(dict.fromkeys([*record["agent_ids"], *scored["agent_ids"]]))
        for branch in survivors:
            if branch["id"] in scored["scores"]:
                rubric = Rubric.model_validate(scored["scores"][branch["id"]]).model_dump()
                branch.update(rubric=rubric, score=sum(rubric.values()), status="scored")
            else:
                branch.update(status="pruned", prune_reason="No valid critic score")
        save_record(database, record, finish=True)
        return {"model_calls": record["model_calls"]}

    def select(state: SearchState):
        record = load(state)
        ordered = ranked(
            [
                branch
                for branch in record["branches"]
                if branch["depth"] == state["search_round"] and branch["status"] == "scored"
            ]
        )
        beam = ordered[: LIMITS["beam_width"]]
        for branch in ordered[LIMITS["beam_width"] :]:
            branch.update(status="pruned", prune_reason="Outside two-branch beam")
        record["beams"].append([branch["id"] for branch in beam])
        dominant = (
            bool(beam)
            and beam[0]["score"] >= 80
            and (len(ordered) == 1 or beam[0]["score"] - ordered[1]["score"] >= 10)
        )
        done = (
            not beam
            or dominant
            or state["search_round"] == 2
            or (record["model_calls"] >= MAX_MODEL_CALLS)
        )
        record["stop_reason"] = (
            "No acceptable branch"
            if not beam
            else "One branch clearly dominates"
            if dominant
            else "One-revision/depth limit"
            if state["search_round"] == 2
            else "Model call budget"
            if done
            else "Refine the two-branch beam once"
        )
        record["selected_id"] = beam[0]["id"] if done and beam else None
        if not done:
            record["round"] = 2
        save_record(database, record, finish=True)
        return {"search_done": done, "search_round": record["round"]}

    def submit(state: SearchState):
        record = load(state)
        selected = next(
            (item for item in record["branches"] if item["id"] == record["selected_id"]), None
        )
        allowed = {
            *record["context"]["evidence_ids"],
            *(str(item["id"]) for item in record["context"]["memory"]),
        }
        errors = (
            hard_errors(database, state, Candidate.model_validate(selected["candidate"]), allowed)
            if selected
            else ["No acceptable branch"]
        )
        record["submission"] = {"depth": 3, "hard_errors": errors}
        record["status"] = (
            "withheld" if errors or selected["candidate"]["fallback"] == "withhold" else "valid"
        )
        record["guidance"] = selected["candidate"] if selected and not errors else None
        save_record(database, record, finish=True)
        return {
            "trace": [
                *state["trace"],
                {
                    "node": "selective_tot",
                    "record_id": record["id"],
                    "status": record["status"],
                    "reason": record["stop_reason"],
                },
            ]
        }

    graph = StateGraph(SearchState)
    for name, node in (
        ("generate", generate),
        ("prune", prune),
        ("critique", critique),
        ("select", select),
        ("submit", submit),
    ):
        graph.add_node(name, node)
    graph.add_edge(START, "generate")
    graph.add_edge("generate", "prune")
    graph.add_edge("prune", "critique")
    graph.add_edge("critique", "select")
    graph.add_conditional_edges(
        "select",
        lambda state: "submit" if state["search_done"] else "generate",
        ["submit", "generate"],
    )
    graph.add_edge("submit", END)
    return graph.compile(checkpointer=checkpointer, interrupt_after=interrupt_after)
