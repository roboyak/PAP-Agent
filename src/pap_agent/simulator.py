"""One local background replay, composed of existing durable PAP episodes."""

import asyncio
from datetime import UTC, datetime, timedelta
from math import ceil
from typing import Literal
from uuid import UUID, uuid4, uuid5

from pydantic import AwareDatetime, BaseModel, Field, model_validator
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from pap_agent.database import Database
from pap_agent.observability import export_summary
from pap_agent.selection import REPLAY_END, REPLAY_START, RunSelection, Wing
from pap_agent.workflow import run_episode


class SimulationRequest(BaseModel):
    wing: Wing = "1.24"
    starts_at: AwareDatetime = Field(default=REPLAY_START, ge=REPLAY_START, lt=REPLAY_END)
    ends_at: AwareDatetime = Field(default=REPLAY_END, gt=REPLAY_START, le=REPLAY_END)
    step_minutes: Literal[15, 60] = 60

    @model_validator(mode="after")
    def ordered_window(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("End must follow start")
        return self


class Simulation(SimulationRequest):
    id: UUID = Field(default_factory=uuid4)
    created_at: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    status: Literal["running", "pausing", "paused", "completed", "failed"] = "running"
    completed_steps: int = 0
    message: str = ""

    @property
    def total_steps(self) -> int:
        return ceil((self.ends_at - self.starts_at).total_seconds() / (self.step_minutes * 60))

    def step_time(self, index: int) -> datetime:
        return self.starts_at + timedelta(minutes=index * self.step_minutes)

    def episode_id(self, index: int) -> UUID:
        # Repeating an interrupted step resumes the same LangGraph thread.
        return uuid5(self.id, str(index))


def save(database: Database, run: Simulation) -> None:
    with database.session() as session:
        session.execute(
            text("""INSERT INTO simulations (id, created_at, payload)
            VALUES (:id, :created_at, CAST(:payload AS jsonb))
            ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload"""),
            {"id": run.id, "created_at": run.created_at, "payload": run.model_dump_json()},
        )


def get(database: Database, run_id: UUID | None = None) -> Simulation | None:
    with database.session() as session:
        query = "SELECT payload FROM simulations"
        query += " WHERE id = :id" if run_id else " ORDER BY created_at DESC LIMIT 1"
        payload = session.execute(text(query), {"id": run_id}).scalar_one_or_none()
    return Simulation.model_validate(payload) if payload else None


def view(database: Database, run: Simulation) -> dict:
    """Read compact result summaries from canonical publications, without copying forecasts."""
    ids = [uuid5(run.episode_id(index), "publication") for index in range(run.completed_steps)]
    with database.session() as session:
        results = (
            session.execute(
                text("""SELECT id AS publication_id, payload->>'episode_id' AS episode_id,
                payload->'selection'->>'replay_at' AS replay_at,
                payload->>'status' AS status, payload->>'reason' AS reason,
                payload->'profile'->>'confidence' AS confidence,
                (payload->'profile'->'intervals'->0->>'available_kw')::float AS available_kw
            FROM pap_publications WHERE id = ANY(:ids)
            ORDER BY payload->'selection'->>'replay_at'"""),
                {"ids": ids},
            )
            .mappings()
            .all()
            if ids
            else []
        )
    return {
        **run.model_dump(mode="json"),
        "total_steps": run.total_steps,
        "next_at": run.step_time(run.completed_steps)
        if run.completed_steps < run.total_steps
        else None,
        "results": [dict(row) for row in results],
    }


class Simulator:
    """Single-process runner: pause at a step boundary; restart requires explicit resume."""

    def __init__(self, database: Database):
        self.database = database
        self.task: asyncio.Task | None = None
        self.recovered = False

    def recover(self) -> None:
        # Lazy so liveness/health still work when PostgreSQL is unavailable at startup.
        if not self.recovered:
            with self.database.session() as session:
                session.execute(
                    text("""UPDATE simulations
                    SET payload = payload || '{"status":"paused",
                        "message":"Service restarted. Resume to continue."}'::jsonb
                    WHERE payload->>'status' IN ('running', 'pausing')""")
                )
            self.recovered = True

    def start(self, request: SimulationRequest) -> Simulation:
        self.ensure_idle()
        run = Simulation(**request.model_dump())
        save(self.database, run)
        self.task = asyncio.create_task(self.run(run.id))
        return run

    def ensure_idle(self) -> None:
        if self.task and not self.task.done():
            raise ValueError("A simulation is already running. Pause it first.")

    def pause(self, run: Simulation) -> Simulation:
        if run.status == "running":
            run.status = "pausing"
            save(self.database, run)
        return run

    def resume(self, run: Simulation) -> Simulation:
        self.ensure_idle()
        if run.status in {"paused", "failed"}:
            run.status, run.message = "running", ""
            save(self.database, run)
            self.task = asyncio.create_task(self.run(run.id))
        return run

    async def run(self, run_id: UUID) -> None:
        try:
            while True:
                run = get(self.database, run_id)
                if run.status == "pausing":
                    run.status = "paused"
                    save(self.database, run)
                if run.status != "running":
                    return
                episode = await run_episode(
                    self.database,
                    "mysolark",
                    episode_id=run.episode_id(run.completed_steps),
                    selection=RunSelection(
                        wing=run.wing, replay_at=run.step_time(run.completed_steps)
                    ),
                )
                await asyncio.to_thread(export_summary, episode)
                run = get(self.database, run_id)  # Honor a pause requested during this step.
                run.completed_steps += 1
                if run.completed_steps == run.total_steps:
                    run.status = "completed"
                elif run.status == "pausing":
                    run.status = "paused"
                save(self.database, run)
                if run.status != "running":
                    return
                await asyncio.sleep(1)  # A short visual beat, not real-time 15/60-minute waiting.
        except asyncio.CancelledError:
            run = get(self.database, run_id)
            if run.status in {"running", "pausing"}:
                run.status = "paused"
                save(self.database, run)
            raise
        except Exception:
            try:
                run = get(self.database, run_id)
                run.status = "failed"
                run.message = "PAP step failed. Check service health, then resume."
                save(self.database, run)
            except SQLAlchemyError:
                # Once storage returns, the next API read exposes saved progress as paused.
                self.recovered = False

    async def close(self) -> None:
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
