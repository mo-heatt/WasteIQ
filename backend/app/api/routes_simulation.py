from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.funnel_simulator import default_naive_region_mix, simulate_region_mix
from app.core.virtual_bunker_map import build_virtual_bunker_map
from app.data.clean_shipments import clean_shipments_with_meta
from app.data.load_challenge1_state import load_challenge1_state
from app.data.load_shipments import ShipmentDataError

router = APIRouter(prefix="/api", tags=["simulation"])


class MixSimulationRequest(BaseModel):
    mix_percentages: dict[str, float] | None = None
    left_pct: float | None = None
    center_pct: float | None = None
    right_pct: float | None = None
    low_pct: float | None = None
    medium_pct: float | None = None
    high_pct: float | None = None
    feed_rate_tonnes_per_hour: float = Field(default=10, gt=0, le=100)
    duration_hours: float = Field(default=2, gt=0, le=24)


def _validate_percentages(percentages: dict[str, float]) -> None:
    total_pct = sum(float(percentages.get(region_id, 0.0)) for region_id in ("LEFT", "CENTER", "RIGHT"))
    if abs(total_pct - 100) > 0.001:
        raise HTTPException(status_code=422, detail="LEFT, CENTER and RIGHT percentages must sum to 100.")


def _dashboard() -> dict[str, Any]:
    shipments, source_meta = clean_shipments_with_meta()
    challenge1_state = load_challenge1_state()
    virtual_map = build_virtual_bunker_map(shipments, challenge1_state)
    return {
        "demo_mode": bool(source_meta.get("demo_mode", False)),
        "data_source_message": source_meta.get("message", ""),
        "challenge1_state": challenge1_state,
        "regions": virtual_map["regions"],
        "virtual_bunker_map": virtual_map,
        "current_cv": virtual_map["current_cv"],
        "risk_status": virtual_map["risk_status"],
        "total_mass_tonnes": virtual_map["total_available_mass_tonnes"],
    }


@router.get("/simulation/default")
def default_simulation() -> dict[str, Any]:
    try:
        dashboard = _dashboard()
    except ShipmentDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    naive = default_naive_region_mix(dashboard["regions"])
    return {"dashboard": dashboard, "simulation": naive["simulation"], "naive_region_mix": naive, "naive_mix": naive}


@router.post("/simulate")
def simulate(request: MixSimulationRequest) -> dict[str, Any]:
    try:
        dashboard = _dashboard()
    except ShipmentDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if request.mix_percentages is not None:
        _validate_percentages(request.mix_percentages)
        simulation = simulate_region_mix(
            dashboard["regions"],
            request.mix_percentages.get("LEFT", 0),
            request.mix_percentages.get("CENTER", 0),
            request.mix_percentages.get("RIGHT", 0),
            request.feed_rate_tonnes_per_hour,
            request.duration_hours,
        )
        return {"dashboard": dashboard, "simulation": simulation}

    left_pct = request.left_pct
    center_pct = request.center_pct
    right_pct = request.right_pct
    if left_pct is None and request.low_pct is not None:
        left_pct = request.low_pct
        center_pct = request.medium_pct
        right_pct = request.high_pct

    if left_pct is None or center_pct is None or right_pct is None:
        raise HTTPException(status_code=422, detail="Provide left_pct, center_pct and right_pct, or mix_percentages.")

    _validate_percentages({"LEFT": left_pct, "CENTER": center_pct, "RIGHT": right_pct})
    simulation = simulate_region_mix(
        dashboard["regions"],
        left_pct,
        center_pct,
        right_pct,
        request.feed_rate_tonnes_per_hour,
        request.duration_hours,
    )
    return {"dashboard": dashboard, "simulation": simulation}
