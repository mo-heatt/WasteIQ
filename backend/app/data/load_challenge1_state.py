from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import settings
from app.data.load_shipments import ShipmentDataError


DEMO_CHALLENGE1_STATE: dict[str, Any] = {
    "timestamp": "demo",
    "source": "Demo Challenge 1 Data",
    "total_fill_percent": 64,
    "regions": [
        {"region_id": "LEFT", "fill_percent": 72, "available_mass_tonnes": 45},
        {"region_id": "CENTER", "fill_percent": 58, "available_mass_tonnes": 60},
        {"region_id": "RIGHT", "fill_percent": 40, "available_mass_tonnes": 32},
    ],
    "is_demo": True,
}


def _normalise_region(region: dict[str, Any]) -> dict[str, Any]:
    return {
        "region_id": str(region.get("region_id", "UNKNOWN")).upper(),
        "fill_percent": float(region.get("fill_percent", 0) or 0),
        "available_mass_tonnes": float(region.get("available_mass_tonnes", 0) or 0),
    }


def _normalise_state(payload: dict[str, Any], is_demo: bool, source_path: Path | None = None) -> dict[str, Any]:
    regions = payload.get("regions")
    if not isinstance(regions, list):
        regions = []

    state = {
        "timestamp": payload.get("timestamp") or ("demo" if is_demo else None),
        "source": payload.get("source") or ("Demo Challenge 1 Data" if is_demo else "challenge_1_bunker_image_model"),
        "total_fill_percent": float(payload.get("total_fill_percent", 0) or 0),
        "regions": [_normalise_region(region) for region in regions if isinstance(region, dict)],
        "is_demo": bool(payload.get("is_demo", is_demo)),
    }
    state["status_label"] = "Demo Challenge 1 Data" if state["is_demo"] else "Real Challenge 1 Output"
    state["source_note"] = (
        "Using mock LEFT/CENTER/RIGHT bunker availability until Challenge 1 writes data/challenge1_bunker_state.json."
        if state["is_demo"]
        else f"Loaded Challenge 1 bunker state from {source_path}."
    )
    return state


def load_challenge1_state(path: Path | None = None) -> dict[str, Any]:
    state_path = path or settings.challenge1_state_path
    if not state_path.exists():
        return _normalise_state(DEMO_CHALLENGE1_STATE, is_demo=True)

    try:
        with state_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except json.JSONDecodeError as exc:
        raise ShipmentDataError(f"Challenge 1 state file is not valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise ShipmentDataError("Challenge 1 state file must contain a JSON object.")

    return _normalise_state(payload, is_demo=bool(payload.get("is_demo", False)), source_path=state_path)
