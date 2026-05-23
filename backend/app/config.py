from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Runtime settings kept deliberately small for a hackathon prototype."""

    app_name: str = "WasteIQ"
    target_cv: float = 10.0
    target_cv_min: float = 9.8
    target_cv_max: float = 10.2
    safe_cv_min: float = 8.0
    safe_cv_max: float = 12.0
    default_feed_rate_tonnes_per_hour: float = 10.0
    default_duration_hours: float = 2.0
    default_crane_grab_tonnes: float = 1.0
    openrouter_api_key: str | None = os.getenv("OPENROUTER_API_KEY")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def shipments_path(self) -> Path:
        configured = os.getenv("SHIPMENTS_PATH")
        if configured:
            return Path(configured).expanduser().resolve()
        return self.project_root / "data" / "shipments.json"

    @property
    def public_shipments_path(self) -> Path:
        return self.project_root / "public-files" / "shipments.json"

    @property
    def challenge1_state_path(self) -> Path:
        configured = os.getenv("CHALLENGE1_STATE_PATH")
        if configured:
            return Path(configured).expanduser().resolve()
        return self.project_root / "data" / "challenge1_bunker_state.json"


settings = Settings()
