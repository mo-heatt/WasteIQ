from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.core.operational_update import build_before_after_next_shipment, build_fuel_blend, build_operator_steps
from app.core.virtual_bunker_map import build_virtual_bunker_map
from app.core.waste_layers import build_waste_layers
from app.data.clean_shipments import clean_shipments_with_meta
from app.data.load_challenge1_state import load_challenge1_state
from app.data.load_shipments import ShipmentDataError

router = APIRouter(prefix="/api", tags=["operations"])


def _context() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    shipments, source_meta = clean_shipments_with_meta()
    challenge1_state = load_challenge1_state()
    return shipments, challenge1_state, source_meta


@router.get("/operations/before-after")
def before_after() -> dict[str, Any]:
    try:
        shipments, challenge1_state, source_meta = _context()
    except ShipmentDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    payload = build_before_after_next_shipment(shipments, challenge1_state)
    return {"demo_mode": bool(source_meta.get("demo_mode", False)), **payload}


@router.get("/operations/fuel-area")
def fuel_area() -> dict[str, Any]:
    try:
        shipments, challenge1_state, source_meta = _context()
    except ShipmentDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    update = build_before_after_next_shipment(shipments, challenge1_state)
    after = update["after"]
    optimized = after["optimized_recommendation"]
    fuel_blend = build_fuel_blend(after["regions"], optimized["simulation"])
    return {
        "demo_mode": bool(source_meta.get("demo_mode", False)),
        "virtual_bunker_map": build_virtual_bunker_map(shipments, challenge1_state),
        "waste_layers": build_waste_layers(after["virtual_bunker_map"]),
        "optimized_recommendation": optimized,
        "fuel_blend": fuel_blend,
        "operator_steps": build_operator_steps(optimized),
    }
