from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.core.cv_calculator import round_cv
from app.core.zone_mix import build_zone_forecast, default_naive_mix, optimize_zone_mix, simulate_zone_mix

router = APIRouter(prefix="/api", tags=["scenarios"])


SCENARIOS: dict[str, dict[str, Any]] = {
    "stable_operation": {
        "scenario_name": "Stable operation",
        "problem_statement": "The bunker is already close to target. WasteIQ recommends a balanced maintenance mix.",
        "zones": {"LOW": (9.0, 90), "MEDIUM": (10.0, 260), "HIGH": (13.5, 80)},
        "judge_story": "Stable case: WasteIQ confirms the plant is under control and keeps all zones available.",
    },
    "low_cv_risk": {
        "scenario_name": "Low CV risk",
        "problem_statement": "Low-CV material is accumulating and the naive feed would pull CV toward weak combustion.",
        "zones": {"LOW": (7.4, 260), "MEDIUM": (9.4, 160), "HIGH": (15.0, 65)},
        "judge_story": "Risk case: WasteIQ increases high-CV contribution before the forecast falls below the lower safe limit.",
    },
    "high_cv_risk": {
        "scenario_name": "High CV risk",
        "problem_statement": "High-CV material is dominating the bunker and the naive feed can overheat the furnace.",
        "zones": {"LOW": (8.4, 90), "MEDIUM": (10.2, 130), "HIGH": (15.8, 245)},
        "judge_story": "Risk case: WasteIQ pulls the feed back toward medium and low CV material to protect stability.",
    },
    "zone_exhaustion_risk": {
        "scenario_name": "Zone exhaustion risk",
        "problem_statement": "The CV looks acceptable, but a naive equal mix drains scarce high-CV reserve too quickly.",
        "zones": {"LOW": (8.1, 190), "MEDIUM": (10.1, 280), "HIGH": (16.0, 16)},
        "judge_story": "Strongest case: the optimizer preserves the high-CV reserve while still meeting the energy target.",
    },
}


def _zone(zone_id: str, avg_cv: float, mass: float, total_mass: float) -> dict[str, Any]:
    names = {
        "LOW": "Low CV Zone",
        "MEDIUM": "Medium / Desired CV Zone",
        "HIGH": "High CV Zone",
    }
    risks = {
        "LOW": "Overusing low-CV material weakens combustion and reduces energy output.",
        "MEDIUM": "Medium CV material is the stabilizing buffer for normal operation.",
        "HIGH": "High-CV material is valuable correction reserve; exhausting it early reduces future control.",
    }
    codes = {
        "LOW": ["demo-low"],
        "MEDIUM": ["200301", "191212"],
        "HIGH": ["180104", "191210", "200307"],
    }
    return {
        "zone_id": zone_id,
        "zone_name": names[zone_id],
        "avg_cv": round_cv(avg_cv),
        "available_mass_tonnes": round(mass, 2),
        "percentage_of_total_mass": round((mass / total_mass) * 100, 1) if total_mass else 0,
        "waste_codes_inside": codes[zone_id],
        "status": "AVAILABLE" if mass > 0 else "DISABLED",
        "risk_if_overused": risks[zone_id],
    }


def _zones_from_definition(definition: dict[str, Any]) -> list[dict[str, Any]]:
    total_mass = sum(float(value[1]) for value in definition["zones"].values())
    return [_zone(zone_id, values[0], values[1], total_mass) for zone_id, values in definition["zones"].items()]


def _current_cv(zones: list[dict[str, Any]]) -> float:
    total_mass = sum(float(zone["available_mass_tonnes"]) for zone in zones)
    if total_mass <= 0:
        return 0.0
    energy = sum(float(zone["avg_cv"]) * float(zone["available_mass_tonnes"]) for zone in zones)
    return round_cv(energy / total_mass)


def _scenario_forecast(scenario_id: str, current_cv: float, optimized_simulation: dict[str, Any]) -> list[dict[str, Any]]:
    if scenario_id == "low_cv_risk":
        return [
            {"label": "Now", "hour": 0, "cv": round_cv(current_cv)},
            {"label": "+30m", "hour": 0.5, "cv": 8.7},
            {"label": "+1h", "hour": 1, "cv": 8.2},
            {"label": "+90m", "hour": 1.5, "cv": 7.8},
            {"label": "+2h", "hour": 2, "cv": 7.5},
        ]
    if scenario_id == "high_cv_risk":
        return [
            {"label": "Now", "hour": 0, "cv": round_cv(current_cv)},
            {"label": "+30m", "hour": 0.5, "cv": 11.2},
            {"label": "+1h", "hour": 1, "cv": 11.8},
            {"label": "+90m", "hour": 1.5, "cv": 12.3},
            {"label": "+2h", "hour": 2, "cv": 12.8},
        ]
    return build_zone_forecast(current_cv, optimized_simulation)


def _build_scenario_payload(scenario_id: str) -> dict[str, Any]:
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Unknown scenario.")

    definition = SCENARIOS[scenario_id]
    zones = _zones_from_definition(definition)
    current_cv = _current_cv(zones)
    naive = default_naive_mix(zones)
    optimized = optimize_zone_mix(zones, settings.default_feed_rate_tonnes_per_hour, settings.default_duration_hours)
    forecast = _scenario_forecast(scenario_id, current_cv, optimized["simulation"])
    recommendation = {
        "action": optimized["explanation"],
        "mix_percentages": optimized["mix_percentages"],
        "expected_cv": optimized["simulation"]["blended_cv"],
        "operator_instruction": "Review the deterministic simulation and approve before changing the feed plan.",
    }
    explanation = {
        "summary": definition["problem_statement"],
        "operator_instruction": recommendation["operator_instruction"],
        "why_this_mix": optimized["explanation"],
        "zone_preservation_reasoning": (
            "The score penalizes exhausting one zone and rejects infeasible feed plans, so reserve material remains available."
        ),
        "safety_note": "This is not autonomous control. It is human-in-the-loop decision support.",
        "confidence": "High for demo: scenario values are deterministic and the optimizer calculation is repeatable.",
    }
    return {
        "scenario_id": scenario_id,
        "scenario_name": definition["scenario_name"],
        "problem_statement": definition["problem_statement"],
        "zone_state": zones,
        "current_cv": current_cv,
        "naive_mix": naive,
        "optimized_mix": optimized,
        "forecast": forecast,
        "recommendation": recommendation,
        "explanation": explanation,
        "judge_story": definition["judge_story"],
    }


@router.get("/scenarios")
def scenarios() -> list[dict[str, str]]:
    return [
        {
            "scenario_id": scenario_id,
            "scenario_name": definition["scenario_name"],
            "problem_statement": definition["problem_statement"],
        }
        for scenario_id, definition in SCENARIOS.items()
    ]


@router.get("/scenarios/{scenario_id}")
def scenario_detail(scenario_id: str) -> dict[str, Any]:
    return _build_scenario_payload(scenario_id)
