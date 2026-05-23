from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["demo"])


@router.get("/demo/steps")
def demo_steps() -> list[dict[str, Any]]:
    return [
        {
            "step": 1,
            "title": "Truck arrives",
            "description": "A truck enters the receiving flow with waste code, weight and timestamp.",
            "visual_type": "shipment_table",
        },
        {
            "step": 2,
            "title": "Waste code mapped to CV",
            "description": "The shipment waste code is mapped to a deterministic calorific value.",
            "visual_type": "waste_mapping",
        },
        {
            "step": 3,
            "title": "Truck enters Receiving Area",
            "description": "WasteIQ shows truck status, waste-code layer and unloading readiness.",
            "visual_type": "truck_assignment",
        },
        {
            "step": 4,
            "title": "WasteIQ recommends unloading region",
            "description": "The preferred region is checked against fill percentage and available mass.",
            "visual_type": "truck_assignment",
        },
        {
            "step": 5,
            "title": "Challenge 1 provides region fill and capacity",
            "description": "LEFT, CENTER and RIGHT availability comes from the Challenge 1 bunker state.",
            "visual_type": "challenge1",
        },
        {
            "step": 6,
            "title": "Virtual 9-layer bunker map updates",
            "description": "Waste-code layers are estimated inside each operational region without rebuilding the bunker.",
            "visual_type": "layers",
        },
        {
            "step": 7,
            "title": "Region average CV updates",
            "description": "LEFT, CENTER and RIGHT average CVs update from the 9-layer composition.",
            "visual_type": "regions",
        },
        {
            "step": 8,
            "title": "Before/after state is shown",
            "description": "WasteIQ compares old bunker state and old recipe against the updated state and recipe.",
            "visual_type": "before_after",
        },
        {
            "step": 9,
            "title": "Optimizer creates 2-hour funnel recipe",
            "description": "The optimizer chooses a safe region-based recipe near 10 MJ/kg while preserving bunker flexibility.",
            "visual_type": "funnel_recipe",
        },
        {
            "step": 10,
            "title": "AI explains and operator approves",
            "description": "The AI explains the deterministic recommendation; the operator remains in control.",
            "visual_type": "approval",
        },
    ]
