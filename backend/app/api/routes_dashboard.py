from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.core.bunker_zones import build_waste_distribution
from app.core.forecast import build_two_hour_forecast
from app.core.funnel_simulator import optimize_region_mix
from app.core.operational_update import build_before_after_next_shipment, build_fuel_blend, build_operator_steps
from app.core.truck_assignment import assign_recent_trucks
from app.core.virtual_bunker_map import build_virtual_bunker_map
from app.core.waste_layers import build_waste_layers
from app.core.zone_builder import current_bunker_summary
from app.data.clean_shipments import clean_shipments_with_meta
from app.data.load_challenge1_state import load_challenge1_state
from app.data.load_shipments import ShipmentDataError

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
def dashboard() -> dict:
    try:
        shipments, source_meta = clean_shipments_with_meta()
    except ShipmentDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    challenge1_state = load_challenge1_state()
    virtual_map = build_virtual_bunker_map(shipments, challenge1_state)
    regions = virtual_map["regions"]
    waste_layers = build_waste_layers(virtual_map)
    legacy_summary = current_bunker_summary(shipments)
    optimized = optimize_region_mix(
        regions,
        settings.default_feed_rate_tonnes_per_hour,
        settings.default_duration_hours,
    )
    payload = {
        "demo_mode": bool(source_meta.get("demo_mode", False)),
        "data_source_message": source_meta.get("message", ""),
        "current_cv": virtual_map["current_cv"],
        "target_cv": settings.target_cv,
        "safe_min": settings.safe_cv_min,
        "safe_max": settings.safe_cv_max,
        "safe_min_cv": settings.safe_cv_min,
        "safe_max_cv": settings.safe_cv_max,
        "risk_status": virtual_map["risk_status"],
        "total_mass_tonnes": virtual_map["total_available_mass_tonnes"],
        "total_available_mass_tonnes": virtual_map["total_available_mass_tonnes"],
        "shipment_count": legacy_summary["shipment_count"],
        "first_timestamp": legacy_summary["first_timestamp"],
        "latest_timestamp": legacy_summary["latest_timestamp"],
        "dominant_waste_code": virtual_map["dominant_waste_layer"],
        "dominant_region": virtual_map["dominant_region"],
        "challenge1_state": challenge1_state,
        "virtual_bunker_map": virtual_map,
        "regions": regions,
        "waste_layers": waste_layers,
        "waste_distribution": build_waste_distribution(shipments),
        "latest_shipments": legacy_summary["latest_shipments"],
    }
    payload["optimized_recommendation"] = optimized
    recent_assignments = assign_recent_trucks(shipments, challenge1_state, regions, limit=10)
    payload["latest_truck_assignment"] = recent_assignments[0] if recent_assignments else None
    payload["recent_truck_assignments"] = recent_assignments
    payload["recommended_mix_summary"] = {
        "mix_percentages": optimized["recommended_region_mix"],
        "expected_cv": optimized["simulation"]["blended_cv"],
        "is_safe": optimized["simulation"]["is_cv_safe"],
        "is_feasible": optimized["simulation"]["is_feasible"],
        "reason": optimized.get("why_this_mix_is_best", ""),
    }
    payload["forecast"] = build_two_hour_forecast(float(virtual_map["current_cv"]), optimized)
    before_after = build_before_after_next_shipment(shipments, challenge1_state)
    payload["before_after_next_shipment"] = before_after
    payload["fuel_blend"] = build_fuel_blend(regions, optimized["simulation"])
    payload["operator_steps"] = build_operator_steps(optimized)
    return payload
