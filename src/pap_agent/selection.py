"""The small, explicit source selection saved with each run."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field

Wing = Literal["1.21", "1.22", "1.23", "1.24", "1.25"]
# Sunday midnight to Sunday midnight in America/Los_Angeles (PDT).
REPLAY_START = datetime(2026, 8, 30, 7, tzinfo=UTC)
REPLAY_END = datetime(2026, 9, 6, 7, tzinfo=UTC)
# Fixed positive minima from the authorized source scan; see docs/data/wing-floors.json.
WING_FLOORS = {"1.21": 313.2, "1.22": 310.3, "1.23": 319.0, "1.24": 305.2, "1.25": 309.8}


class RunSelection(BaseModel):
    wing: Wing = "1.24"
    replay_at: AwareDatetime | None = Field(default=None, ge=REPLAY_START, lt=REPLAY_END)

    def feedback_scope(self, data_mode: str) -> str:
        if data_mode == "synthetic":
            return "synthetic"
        if self.replay_at:
            return "general"  # Snapshot replay uses guidance, never later observed outcomes.
        return "live" if self.wing == "1.24" else f"live:{self.wing}"
