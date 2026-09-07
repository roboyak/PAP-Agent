"""Opt-in summary export. Full local prompts, telemetry and memory never leave this path."""

import logging
from datetime import UTC, datetime

from langsmith import Client
from urllib3.util import Retry

from pap_agent.config import Settings


def export_summary(episode: dict) -> None:
    settings = Settings()
    if not settings.enable_langsmith:
        return
    try:
        client = Client(
            api_key=settings.langsmith_api_key.get_secret_value()
            if settings.langsmith_api_key
            else None,
            auto_batch_tracing=False,
            timeout_ms=1000,
            retry_config=Retry(total=0),
            omit_traced_runtime_info=True,
        )
        try:
            now = datetime.now(UTC)
            client.create_run(
                "PAP summary",
                inputs={"episode_id": episode["episode_id"]},
                run_type="chain",
                project_name=settings.langsmith_project,
                outputs={
                    key: episode.get(key)
                    for key in ("publication_id", "status", "reasoning_mode", "model_calls")
                },
                start_time=now,
                end_time=now,
                tags=[settings.pap_profile, episode["scenario"]],
            )
        finally:
            client.close(timeout=1)
    except Exception:
        # Optional provider SDK/export failures must never change a published decision.
        logging.getLogger("uvicorn.error").warning("Optional summary export unavailable")
