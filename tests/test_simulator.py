import asyncio
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from pap_agent import simulator
from pap_agent.simulator import Simulation, SimulationRequest, Simulator, get, save, view
from pap_agent.store import get_episode


def request():
    return SimulationRequest(
        wing="1.21",
        starts_at=datetime(2026, 8, 30, 19, tzinfo=UTC),
        ends_at=datetime(2026, 8, 30, 19, 45, tzinfo=UTC),
        step_minutes=15,
    )


def test_simulator_runs_real_workflow_to_end(database, wing_history):
    async def exercise():
        runner = Simulator(database)
        runner.recover()
        run = runner.start(request())
        await runner.task
        result = view(database, get(database, run.id))
        assert result["status"] == "completed"
        assert result["completed_steps"] == result["total_steps"] == 3
        assert result["next_at"] is None
        assert [row["status"] for row in result["results"]] == ["valid", "valid", "withheld"]
        assert [row["available_kw"] for row in result["results"]] == [1.6, 1.2, None]
        for index, row in enumerate(result["results"]):
            episode = get_episode(database, run.episode_id(index))
            assert row["episode_id"] == episode["episode_id"]
            assert episode["selection"]["wing"] == "1.21"
            assert datetime.fromisoformat(row["replay_at"]) == run.step_time(index)
        with database.session() as session:
            assert session.execute(text("SELECT count(*) FROM pap_publications")).scalar_one() == 3
            assert session.execute(text("SELECT count(*) FROM outcome_records")).scalar_one() == 0

    asyncio.run(exercise())


def test_pause_finishes_step_and_resume_keeps_progress(database, wing_history, monkeypatch):
    async def exercise():
        entered, finish = asyncio.Event(), asyncio.Event()
        original = simulator.run_episode

        async def held_step(*args, **kwargs):
            entered.set()
            await finish.wait()
            return await original(*args, **kwargs)

        monkeypatch.setattr(simulator, "run_episode", held_step)
        runner = Simulator(database)
        runner.recover()
        run = runner.start(request())
        await entered.wait()
        assert runner.pause(get(database, run.id)).status == "pausing"
        finish.set()
        await runner.task
        paused = get(database, run.id)
        assert paused.status == "paused"
        assert paused.completed_steps == 1
        runner.resume(paused)
        await runner.task
        assert get(database, run.id).status == "completed"
        with database.session() as session:
            assert session.execute(text("SELECT count(*) FROM episode_records")).scalar_one() == 3

    asyncio.run(exercise())


def test_restart_resumes_completed_step_without_duplicate(database, wing_history, monkeypatch):
    async def exercise():
        completed = asyncio.Event()
        original = simulator.run_episode

        async def interrupted_after_publication(*args, **kwargs):
            await original(*args, **kwargs)
            completed.set()
            await asyncio.Event().wait()

        monkeypatch.setattr(simulator, "run_episode", interrupted_after_publication)
        runner = Simulator(database)
        runner.recover()
        run = runner.start(request())
        await completed.wait()
        await runner.close()
        assert get(database, run.id).completed_steps == 0
        # Emulate the persisted state left by an abrupt process exit, not a clean shutdown.
        save(database, Simulation(**run.model_dump()))
        restarted = Simulator(database)
        restarted.recover()
        paused = get(database, run.id)
        assert paused.status == "paused"
        assert "restarted" in paused.message
        monkeypatch.setattr(simulator, "run_episode", original)
        restarted.resume(paused)
        await restarted.task
        assert get(database, run.id).completed_steps == 3
        with database.session() as session:
            assert session.execute(text("SELECT count(*) FROM episode_records")).scalar_one() == 3
            assert session.execute(text("SELECT count(*) FROM pap_publications")).scalar_one() == 3

    asyncio.run(exercise())


def test_database_returns_after_worker_stops(database, wing_history, monkeypatch):
    async def exercise():
        original_get, original_run = simulator.get, simulator.run_episode
        unavailable = False

        def interrupted_store(*args, **kwargs):
            if unavailable:
                raise SQLAlchemyError("Test database interruption")
            return original_get(*args, **kwargs)

        async def lost_database(*args, **kwargs):
            nonlocal unavailable
            unavailable = True
            raise SQLAlchemyError("Test database interruption")

        monkeypatch.setattr(simulator, "get", interrupted_store)
        monkeypatch.setattr(simulator, "run_episode", lost_database)
        runner = Simulator(database)
        runner.recover()
        run = runner.start(request())
        await runner.task
        assert original_get(database, run.id).status == "running"
        unavailable = False
        runner.recover()  # The same recovery called by the next successful API poll.
        paused = get(database, run.id)
        assert paused.status == "paused"
        monkeypatch.setattr(simulator, "run_episode", original_run)
        runner.resume(paused)
        await runner.task
        assert get(database, run.id).status == "completed"

    asyncio.run(exercise())
