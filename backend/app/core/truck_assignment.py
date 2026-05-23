from __future__ import annotations

from typing import Any

from app.core.region_mapper import REGION_MEANINGS, preferred_region_for_cv, recommend_unloading_region


def _regions_by_id(challenge1_state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(region.get("region_id", "")).upper(): {
            "region_id": str(region.get("region_id", "")).upper(),
            "fill_percent": float(region.get("fill_percent", 0) or 0),
            "available_mass_tonnes": float(region.get("available_mass_tonnes", 0) or 0),
        }
        for region in challenge1_state.get("regions", [])
        if isinstance(region, dict)
    }


def _best_available_region(regions: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    if not regions:
        return None
    return max(regions.values(), key=lambda region: float(region.get("available_mass_tonnes", 0) or 0))


def _region_has_capacity(region: dict[str, Any] | None, weight_tonnes: float) -> bool:
    if not region:
        return False
    fill_percent = float(region.get("fill_percent", 0) or 0)
    available_mass = float(region.get("available_mass_tonnes", 0) or 0)
    return fill_percent < 85 and available_mass >= weight_tonnes


def assign_incoming_truck(
    shipment: dict[str, Any],
    challenge1_state: dict[str, Any],
    current_zone_state: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Recommend where an arriving truck should unload inside the open bunker."""

    cv = float(shipment.get("cv", 10.0) or 10.0)
    weight_tonnes = float(shipment.get("weight_tonnes", 0.0) or 0.0)
    preferred_region_id = preferred_region_for_cv(cv)
    recommendation = recommend_unloading_region(cv, weight_tonnes, challenge1_state)
    selected_region_id = recommendation["recommended_unloading_region"]
    operational_meaning = REGION_MEANINGS.get(selected_region_id, "guided unloading region")
    truck_id = shipment.get("truck_id") or "Unknown truck"
    return {
        "truck_id": truck_id,
        "timestamp": shipment.get("timestamp"),
        "waste_code": shipment.get("waste_code", "UNKNOWN"),
        "waste_name": shipment.get("waste_name", "Unknown waste code"),
        "weight_tonnes": round(weight_tonnes, 2),
        "cv": round(cv, 2),
        "waste_layer_id": shipment.get("waste_layer_id") or shipment.get("waste_code", "UNKNOWN"),
        "cv_category": "LOWER" if cv < 10 else ("MEDIUM" if cv <= 13 else "HIGH"),
        "recommended_unloading_region": selected_region_id,
        "recommended_region_meaning": operational_meaning,
        "preferred_region": preferred_region_id,
        "preferred_region_meaning": REGION_MEANINGS.get(preferred_region_id, "guided unloading region"),
        "fallback_used": recommendation["fallback_used"],
        "reason": (
            f"Waste code {shipment.get('waste_code', 'UNKNOWN')} is mapped to the {shipment.get('waste_layer_id') or shipment.get('waste_code', 'UNKNOWN')} "
            f"virtual waste-code layer. {recommendation['reason']}"
        ),
        "operator_instruction": f"Direct truck {truck_id} to unload near the {selected_region_id} operational region.",
        "capacity_warning": recommendation["capacity_warning"],
        "challenge1_source": challenge1_state.get("status_label") or challenge1_state.get("source"),
        "virtual_map_update": (
            f"Track {round(weight_tonnes, 2)} t from truck {truck_id} as waste-code layer "
            f"{shipment.get('waste_code', 'UNKNOWN')} expected near the {selected_region_id} operational region."
        ),
        "region_fill_percent": recommendation["region_fill_percent"],
        "region_available_mass_tonnes": recommendation["region_available_mass_tonnes"],
    }


def assign_recent_trucks(
    shipments: list[dict[str, Any]],
    challenge1_state: dict[str, Any],
    current_zone_state: list[dict[str, Any]] | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    latest_shipments = sorted(shipments, key=lambda item: item.get("timestamp", ""), reverse=True)[:limit]
    return [assign_incoming_truck(shipment, challenge1_state, current_zone_state) for shipment in latest_shipments]
