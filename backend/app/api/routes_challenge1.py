from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.data.load_challenge1_state import load_challenge1_state
from app.data.load_shipments import ShipmentDataError

router = APIRouter(prefix="/api", tags=["challenge1"])


@router.get("/challenge1/state")
def challenge1_state() -> dict:
    try:
        return load_challenge1_state()
    except ShipmentDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
