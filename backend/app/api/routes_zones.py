from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.core.zone_builder import build_virtual_zones, current_bunker_summary
from app.data.clean_shipments import clean_shipments_with_meta
from app.data.load_challenge1_state import load_challenge1_state
from app.data.load_shipments import ShipmentDataError

router = APIRouter(prefix="/api", tags=["zones"])


@router.get("/zones")
def zones() -> dict[str, Any]:
    try:
        shipments, source_meta = clean_shipments_with_meta()
    except ShipmentDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    challenge1_state = load_challenge1_state()
    zones_payload = build_virtual_zones(shipments, challenge1_state)
    summary = current_bunker_summary(shipments)
    return {
        "demo_mode": bool(source_meta.get("demo_mode", False)),
        "challenge1_state": challenge1_state,
        "zones": zones_payload,
        "current_cv": summary["current_cv"],
        "total_mass_tonnes": summary["total_mass_tonnes"],
        "risk_status": summary["risk_status"],
    }
