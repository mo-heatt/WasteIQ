from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.core.virtual_bunker_map import build_virtual_bunker_map
from app.data.clean_shipments import clean_shipments_with_meta
from app.data.load_challenge1_state import load_challenge1_state
from app.data.load_shipments import ShipmentDataError
from app.api.routes_optimizer import build_optimizer_comparison

router = APIRouter(prefix="/api", tags=["impact"])


@router.get("/impact")
def impact() -> dict[str, Any]:
    try:
        shipments, source_meta = clean_shipments_with_meta()
    except ShipmentDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    challenge1_state = load_challenge1_state()
    virtual_map = build_virtual_bunker_map(shipments, challenge1_state)
    dashboard = {
        "demo_mode": bool(source_meta.get("demo_mode", False)),
        "challenge1_state": challenge1_state,
        "virtual_bunker_map": virtual_map,
        "regions": virtual_map["regions"],
        "current_cv": virtual_map["current_cv"],
        "risk_status": virtual_map["risk_status"],
        "total_mass_tonnes": virtual_map["total_available_mass_tonnes"],
    }
    comparison = build_optimizer_comparison(dashboard)
    naive = comparison["naive_mix"]["simulation"]
    optimized = comparison["optimized_mix"]["simulation"]
    unsafe_mix_avoided = (not naive["is_cv_safe"]) or (not naive["is_feasible"] and optimized["is_feasible"])

    return {
        "cv_target": settings.target_cv,
        "target_cv": settings.target_cv,
        "safe_range": "8-12 MJ/kg",
        "safe_band": "8-12 MJ/kg",
        "naive_target_error": naive["target_error"],
        "optimized_target_error": optimized["target_error"],
        "region_preservation_improvement_percent": comparison["improvement_summary"]["region_preservation_improvement_percent"],
        "zone_preservation_improvement_percent": comparison["improvement_summary"]["region_preservation_improvement_percent"],
        "unsafe_mix_avoided": unsafe_mix_avoided,
        "operator_decision_time": "under 10 seconds",
        "summary": (
            "WasteIQ uses shipment records and Challenge 1 bunker availability to create a software-defined 9-layer energy map, then recommends a safe region-based funnel recipe."
        ),
    }
