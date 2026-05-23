from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.core.funnel_simulator import default_naive_region_mix, optimize_region_mix
from app.core.virtual_bunker_map import build_virtual_bunker_map
from app.data.clean_shipments import clean_shipments_with_meta
from app.data.load_challenge1_state import load_challenge1_state
from app.data.load_shipments import ShipmentDataError

router = APIRouter(prefix="/api", tags=["optimizer"])


def build_optimizer_comparison(dashboard: dict[str, Any]) -> dict[str, Any]:
    naive = default_naive_region_mix(dashboard["regions"])
    optimized = optimize_region_mix(
        dashboard["regions"],
        settings.default_feed_rate_tonnes_per_hour,
        settings.default_duration_hours,
    )
    naive_error = float(naive["simulation"]["target_error"])
    optimized_error = float(optimized["simulation"]["target_error"])
    naive_exhaustion = float(naive["simulation"]["max_exhaustion_risk"])
    optimized_exhaustion = float(optimized["simulation"]["max_exhaustion_risk"])
    preservation_delta = max(0.0, naive_exhaustion - optimized_exhaustion)

    return {
        "naive_mix": naive,
        "optimized_mix": optimized,
        "improvement_summary": {
            "target_error_reduction": round(max(0.0, naive_error - optimized_error), 2),
            "region_preservation_improvement_percent": round(preservation_delta * 100, 1),
            "zone_preservation_improvement_percent": round(preservation_delta * 100, 1),
            "score_reduction": round(max(0.0, float(naive["score"]) - float(optimized["score"])), 2),
        },
        "why_optimized_is_better": (
            "The optimized mix keeps CV near target while preserving bunker flexibility. "
            "It rejects infeasible mixes, penalizes unsafe CV, and reduces dependency on any one region."
        ),
    }


@router.get("/optimizer/comparison")
def optimizer_comparison() -> dict[str, Any]:
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
    return {
        "dashboard": dashboard,
        **comparison,
        "naive_region_mix_result": comparison["naive_mix"],
        "optimized_region_mix_result": comparison["optimized_mix"],
        "naive_mix_result": comparison["naive_mix"],
        "optimized_mix_result": comparison["optimized_mix"],
    }
