from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.truck_assignment import assign_incoming_truck, assign_recent_trucks
from app.core.virtual_bunker_map import build_virtual_bunker_map
from app.core.zone_builder import assign_cv_zone
from app.data.clean_shipments import clean_shipments_with_meta
from app.data.load_challenge1_state import load_challenge1_state
from app.data.load_shipments import ShipmentDataError
from app.data.waste_code_mapping import cv_for_waste_code, name_for_waste_code, normalize_waste_code

router = APIRouter(prefix="/api/truck-assignment", tags=["truck-assignment"])


class TruckAssignmentSimulationRequest(BaseModel):
    waste_code: str = Field(default="191210")
    weight_tonnes: float = Field(default=10, gt=0, le=100)
    truck_id: str = Field(default="TRUCK-DEMO")


def _assignment_context() -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    shipments, source_meta = clean_shipments_with_meta()
    challenge1_state = load_challenge1_state()
    regions = build_virtual_bunker_map(shipments, challenge1_state)["regions"]
    return shipments, challenge1_state, regions, source_meta


@router.get("/latest")
def latest_truck_assignment() -> dict[str, Any]:
    try:
        shipments, challenge1_state, zones, source_meta = _assignment_context()
    except ShipmentDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not shipments:
        raise HTTPException(status_code=404, detail="No shipment rows are available for truck assignment.")

    latest_shipment = sorted(shipments, key=lambda item: item.get("timestamp", ""), reverse=True)[0]
    return {
        "demo_mode": bool(source_meta.get("demo_mode", False)),
        "assignment": assign_incoming_truck(latest_shipment, challenge1_state, zones),
    }


@router.get("/recent")
def recent_truck_assignments() -> dict[str, Any]:
    try:
        shipments, challenge1_state, zones, source_meta = _assignment_context()
    except ShipmentDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "demo_mode": bool(source_meta.get("demo_mode", False)),
        "assignments": assign_recent_trucks(shipments, challenge1_state, zones, limit=10),
    }


@router.post("/simulate")
def simulate_truck_assignment(request: TruckAssignmentSimulationRequest) -> dict[str, Any]:
    try:
        shipments, challenge1_state, zones, source_meta = _assignment_context()
    except ShipmentDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    waste_code = normalize_waste_code(request.waste_code)
    cv = cv_for_waste_code(waste_code)
    shipment = {
        "truck_id": request.truck_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "waste_code": waste_code,
        "waste_name": name_for_waste_code(waste_code),
        "weight_tonnes": request.weight_tonnes,
        "weight_kg": request.weight_tonnes * 1000,
        "cv": cv,
        "energy_mj": request.weight_tonnes * 1000 * cv,
        "waste_layer_id": waste_code,
        "assigned_cv_zone": assign_cv_zone(cv),
    }
    return {
        "demo_mode": bool(source_meta.get("demo_mode", False)),
        "assignment": assign_incoming_truck(shipment, challenge1_state, zones),
    }
