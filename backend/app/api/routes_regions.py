from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.core.virtual_bunker_map import build_virtual_bunker_map
from app.data.clean_shipments import clean_shipments_with_meta
from app.data.load_challenge1_state import load_challenge1_state
from app.data.load_shipments import ShipmentDataError

router = APIRouter(prefix="/api", tags=["regions"])


@router.get("/regions")
def regions() -> dict[str, Any]:
    try:
        shipments, source_meta = clean_shipments_with_meta()
    except ShipmentDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    challenge1_state = load_challenge1_state()
    virtual_map = build_virtual_bunker_map(shipments, challenge1_state)
    return {
        "demo_mode": bool(source_meta.get("demo_mode", False)),
        "challenge1_state": challenge1_state,
        **virtual_map,
    }
