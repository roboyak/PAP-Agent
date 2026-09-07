from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from pap_agent import __version__
from pap_agent.config import Settings
from pap_agent.database import Database
from pap_agent.domain import Scenario
from pap_agent.store import get_scenario, list_scenarios

STATIC_DIR = Path(__file__).with_name("static")


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
        return {"version": __version__, "read_only": True, "mode": "synthetic"}

    @app.get("/api/v1/scenarios")
    def scenarios() -> list[dict]:
        return list_scenarios(app.state.database)

    @app.get("/api/v1/scenarios/{name}")
    def scenario(name: str) -> Scenario:
        result = get_scenario(app.state.database, name)
        if result is None:
            raise HTTPException(404, "Scenario not found; run make seed")
        return result

    return app


app = create_app()
