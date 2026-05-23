from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.agent.explanation_agent import create_agent_explanation
from app.config import settings
from app.core.forecast import build_two_hour_forecast
from app.core.funnel_simulator import optimize_region_mix
from app.core.operational_update import build_before_after_next_shipment, build_fuel_blend, build_operator_steps
from app.core.virtual_bunker_map import build_virtual_bunker_map
from app.core.waste_layers import build_waste_layers
from app.core.zone_builder import current_bunker_summary
from app.data.clean_shipments import clean_shipments_with_meta
from app.data.load_challenge1_state import load_challenge1_state
from app.data.load_shipments import ShipmentDataError

router = APIRouter(prefix="/api", tags=["recommendation"])


@router.get("/recommendation")
async def recommendation() -> dict[str, Any]:
    try:
        shipments, source_meta = clean_shipments_with_meta()
    except ShipmentDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    challenge1_state = load_challenge1_state()
    virtual_map = build_virtual_bunker_map(shipments, challenge1_state)
    regions = virtual_map["regions"]
    waste_layers = build_waste_layers(virtual_map)
    legacy_summary = current_bunker_summary(shipments)
    dashboard = {
        "demo_mode": bool(source_meta.get("demo_mode", False)),
        "data_source_message": source_meta.get("message", ""),
        "challenge1_state": challenge1_state,
        "virtual_bunker_map": virtual_map,
        "regions": regions,
        "waste_layers": waste_layers,
        "current_cv": virtual_map["current_cv"],
        "risk_status": virtual_map["risk_status"],
        "total_mass_tonnes": virtual_map["total_available_mass_tonnes"],
        "latest_shipments": legacy_summary["latest_shipments"],
    }
    optimized_region_mix = optimize_region_mix(
        regions,
        settings.default_feed_rate_tonnes_per_hour,
        settings.default_duration_hours,
    )
    simulation = optimized_region_mix["simulation"]
    forecast = build_two_hour_forecast(float(dashboard["current_cv"]), optimized_region_mix)
    payload = {
        "dashboard": dashboard,
        "optimized_mix": optimized_region_mix,
        "optimized_region_mix": optimized_region_mix,
        "simulation": simulation,
        "forecast": forecast,
        "before_after_next_shipment": build_before_after_next_shipment(shipments, challenge1_state),
        "fuel_blend": build_fuel_blend(regions, simulation),
        "operator_steps": build_operator_steps(optimized_region_mix),
    }
    explanation = await create_agent_explanation(payload)
    return {
        **payload,
        "simulation_result": simulation,
        "region_forecast": forecast,
        "agent": explanation,
        "agent_explanation": explanation,
    }
