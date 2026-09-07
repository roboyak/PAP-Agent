from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from uuid import UUID

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from pap_agent import __version__
from pap_agent.config import Settings
from pap_agent.core import Calculation, calculate
from pap_agent.database import Database
from pap_agent.domain import Scenario
from pap_agent.evidence import Evidence, acquire
from pap_agent.store import (
    get_calculation,
    get_episode,
    get_evidence,
    get_scenario,
    list_scenarios,
    save_calculation,
)
from pap_agent.workflow import PAPGraphState, run_episode

STATIC_DIR = Path(__file__).with_name("static")


class RunRequest(BaseModel):
    scenario: Literal["sunny", "mysolark"] = "mysolark"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.database = Database(settings)
        try:
            yield
        finally:
            app.state.database.close()

    app = FastAPI(title="DragonWings PAP Forecaster", version=__version__, lifespan=lifespan)

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def home() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health")
    def health(response: Response) -> dict[str, str]:
        try:
            if app.state.database.has_pgvector():
                return {"status": "ok", "database": "ok", "pgvector": "ok"}
            result = {"status": "unavailable", "database": "ok", "pgvector": "missing"}
        except SQLAlchemyError:
            # Database errors can contain connection details; return status only.
            result = {
                "status": "unavailable",
                "database": "unavailable",
                "pgvector": "unavailable",
            }
        response.status_code = 503
        return result

    @app.get("/api/v1/version")
    def version() -> dict[str, str | bool]:
        return {"version": __version__, "read_only": True, "mode": "local"}

    @app.get("/api/v1/scenarios")
    def scenarios() -> list[dict]:
        return list_scenarios(app.state.database)

    @app.get("/api/v1/evidence/current")
    async def current_evidence(scenario: Literal["sunny", "mysolark"] = "sunny") -> Evidence:
        return await acquire(app.state.database, scenario)

    @app.get("/api/v1/scenarios/{name}")
    def scenario(name: str) -> Scenario:
        result = get_scenario(app.state.database, name)
        if result is None:
            raise HTTPException(404, "Scenario not found; run make seed")
        return result

    @app.get("/api/v1/evidence/{record_id}")
    def evidence_record(record_id: UUID) -> Evidence:
        result = get_evidence(app.state.database, record_id)
        if result is None:
            raise HTTPException(404, "Evidence not found")
        return Evidence.model_validate(result)

    @app.post("/api/v1/pap/calculate")
    async def calculate_pap(request: RunRequest) -> Calculation:
        evidence = await acquire(app.state.database, request.scenario)
        result = calculate(evidence)
        save_calculation(app.state.database, result.model_dump(mode="json"))
        return result

    @app.get("/api/v1/calculations/{record_id}")
    def calculation(record_id: UUID) -> Calculation:
        result = get_calculation(app.state.database, record_id)
        if result is None:
            raise HTTPException(404, "Calculation not found")
        return Calculation.model_validate(result)

    @app.post("/api/v1/pap/run")
    async def run_pap(request: RunRequest) -> PAPGraphState:
        return await run_episode(app.state.database, request.scenario)

    @app.get("/api/v1/episodes/{episode_id}")
    def episode(episode_id: UUID) -> PAPGraphState:
        result = get_episode(app.state.database, episode_id)
        if result is None:
            raise HTTPException(404, "Completed episode not found")
        return result

    @app.post("/api/v1/episodes/{episode_id}/resume")
    async def resume_episode(episode_id: UUID) -> PAPGraphState:
        return await run_episode(app.state.database, episode_id=episode_id)

    return app


app = create_app()
