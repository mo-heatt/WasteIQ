from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.config import settings
from app.core.forecast import build_two_hour_forecast
from app.core.funnel_simulator import optimize_region_mix
from app.core.region_mapper import REGION_IDS, preferred_region_for_cv
from app.core.truck_assignment import assign_incoming_truck
from app.core.virtual_bunker_map import build_virtual_bunker_map
from app.core.waste_layers import build_waste_layers
from app.data.waste_code_mapping import cv_for_waste_code, name_for_waste_code


def _estimated_capacity(region: dict[str, Any]) -> float:
    available = float(region.get("available_mass_tonnes", 0) or 0)
    fill = float(region.get("fill_percent", 0) or 0)
    if fill <= 0:
        return max(available, 1.0)
    return max(available / (fill / 100), available, 1.0)


def adjust_region_mass(challenge1_state: dict[str, Any], region_id: str, delta_tonnes: float) -> dict[str, Any]:
    state = deepcopy(challenge1_state)
    for region in state.get("regions", []):
        if str(region.get("region_id", "")).upper() != region_id:
            continue
        capacity = _estimated_capacity(region)
        updated_mass = max(float(region.get("available_mass_tonnes", 0) or 0) + delta_tonnes, 0.0)
        region["available_mass_tonnes"] = round(updated_mass, 2)
        region["fill_percent"] = round(min((updated_mass / capacity) * 100, 100), 1)
    if state.get("regions"):
        state["total_fill_percent"] = round(
            sum(float(region.get("fill_percent", 0) or 0) for region in state["regions"]) / len(state["regions"]),
            1,
        )
    return state


def build_operational_state(shipments: list[dict[str, Any]], challenge1_state: dict[str, Any]) -> dict[str, Any]:
    virtual_map = build_virtual_bunker_map(shipments, challenge1_state)
    optimized = optimize_region_mix(
        virtual_map["regions"],
        settings.default_feed_rate_tonnes_per_hour,
        settings.default_duration_hours,
    )
    return {
        "virtual_bunker_map": virtual_map,
        "regions": virtual_map["regions"],
        "waste_layers": build_waste_layers(virtual_map),
        "optimized_recommendation": optimized,
        "forecast": build_two_hour_forecast(float(virtual_map["current_cv"]), optimized),
    }


def build_fuel_blend(regions: list[dict[str, Any]], simulation: dict[str, Any]) -> dict[str, Any]:
    consumed_by_region = simulation.get("consumed_by_region", {})
    composition_by_code: dict[str, dict[str, Any]] = {}

    for region in regions:
        region_id = region["region_id"]
        consumed = float(consumed_by_region.get(region_id, 0) or 0)
        if consumed <= 0:
            continue
        for layer in region.get("waste_layer_composition", []):
            pct = float(layer.get("percentage_of_region", 0) or 0) / 100
            layer_mass = consumed * pct
            if layer_mass <= 0:
                continue
            code = layer["waste_code"]
            existing = composition_by_code.setdefault(
                code,
                {
                    "waste_code": code,
                    "name": name_for_waste_code(code),
                    "cv": cv_for_waste_code(code),
                    "estimated_mass_tonnes": 0.0,
                },
            )
            existing["estimated_mass_tonnes"] += layer_mass

    total_mass = sum(item["estimated_mass_tonnes"] for item in composition_by_code.values())
    total_energy = sum(item["estimated_mass_tonnes"] * 1000 * item["cv"] for item in composition_by_code.values())
    composition = []
    for item in composition_by_code.values():
        mass = float(item["estimated_mass_tonnes"])
        composition.append(
            {
                **item,
                "estimated_mass_tonnes": round(mass, 2),
                "percentage_of_fuel_mix": round((mass / total_mass) * 100, 1) if total_mass else 0,
            }
        )

    return {
        "pulled_mass_by_region": {region: round(float(consumed_by_region.get(region, 0) or 0), 2) for region in REGION_IDS},
        "waste_code_composition": sorted(composition, key=lambda item: item["estimated_mass_tonnes"], reverse=True),
        "average_cv": round((total_energy / (total_mass * 1000)) if total_mass else 0, 2),
        "total_mass_tonnes": round(total_mass, 2),
        "is_safe": bool(simulation.get("is_cv_safe", False)),
        "furnace_ready_status": "READY FOR FURNACE" if simulation.get("is_cv_safe") and simulation.get("is_feasible") else "OPERATOR REVIEW REQUIRED",
    }


def build_operator_steps(optimized: dict[str, Any]) -> list[dict[str, Any]]:
    consumed = optimized.get("simulation", {}).get("consumed_by_region", {})
    cv = optimized.get("expected_cv")
    return [
        {
            "step": 1,
            "instruction": f"Pull {consumed.get('LEFT', 0):.1f}t from LEFT region.",
            "keywords": ["BASE LOAD", "STABILIZE"],
        },
        {
            "step": 2,
            "instruction": f"Add {consumed.get('CENTER', 0):.1f}t from CENTER region.",
            "keywords": ["MID CV", "BALANCE"],
        },
        {
            "step": 3,
            "instruction": f"Add {consumed.get('RIGHT', 0):.1f}t from RIGHT region.",
            "keywords": ["HIGH CV", "CONTROLLED BOOST"],
        },
        {
            "step": 4,
            "instruction": f"Verify projected blend CV is {cv} MJ/kg and remains inside 8-12.",
            "keywords": ["VERIFY", "SAFE BAND"],
        },
        {
            "step": 5,
            "instruction": "Release fuel mix to furnace after operator approval.",
            "keywords": ["APPROVE", "FURNACE READY"],
        },
    ]


def build_before_after_next_shipment(shipments: list[dict[str, Any]], challenge1_state: dict[str, Any]) -> dict[str, Any]:
    ordered = sorted(shipments, key=lambda item: item.get("timestamp", ""))
    if not ordered:
        empty_state = build_operational_state([], challenge1_state)
        return {
            "before": empty_state,
            "next_shipment": None,
            "assignment": None,
            "after": empty_state,
            "old_funnel_recipe": empty_state["optimized_recommendation"],
            "new_funnel_recipe": empty_state["optimized_recommendation"],
            "feed_plan_change": "No shipment data is available.",
        }

    next_shipment = ordered[-1]
    before_shipments = ordered[:-1]
    preferred_region = preferred_region_for_cv(float(next_shipment.get("cv", 10) or 10))
    before_challenge = adjust_region_mass(challenge1_state, preferred_region, -float(next_shipment.get("weight_tonnes", 0) or 0))
    before = build_operational_state(before_shipments, before_challenge)
    assignment = assign_incoming_truck(next_shipment, before_challenge, before["regions"])
    after_challenge = adjust_region_mass(before_challenge, assignment["recommended_unloading_region"], float(next_shipment.get("weight_tonnes", 0) or 0))
    after = build_operational_state(ordered, after_challenge)

    old_mix = before["optimized_recommendation"].get("recommended_region_mix", {})
    new_mix = after["optimized_recommendation"].get("recommended_region_mix", {})
    changed_parts = [
        f"{region}: {old_mix.get(region, 0):.0f}% -> {new_mix.get(region, 0):.0f}%"
        for region in REGION_IDS
        if round(float(old_mix.get(region, 0)), 1) != round(float(new_mix.get(region, 0)), 1)
    ]
    feed_plan_change = (
        "Feed recipe changed after the latest truck: " + ", ".join(changed_parts)
        if changed_parts
        else "Feed recipe remains stable after the latest truck."
    )

    return {
        "before": before,
        "next_shipment": next_shipment,
        "assignment": assignment,
        "after": after,
        "old_funnel_recipe": before["optimized_recommendation"],
        "new_funnel_recipe": after["optimized_recommendation"],
        "feed_plan_change": feed_plan_change,
    }
