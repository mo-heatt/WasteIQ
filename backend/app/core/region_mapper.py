from __future__ import annotations

from typing import Any


REGION_IDS = ("LEFT", "CENTER", "RIGHT")
REGION_MEANINGS = {
    "LEFT": "lower / medium-low CV guided unloading region",
    "CENTER": "medium CV guided unloading region",
    "RIGHT": "high CV guided unloading region",
}


def preferred_region_for_cv(cv: float) -> str:
    if cv < 10:
        return "LEFT"
    if cv <= 13:
        return "CENTER"
    return "RIGHT"


def regions_by_id(challenge1_state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    regions: dict[str, dict[str, Any]] = {}
    for region in challenge1_state.get("regions", []):
        if not isinstance(region, dict):
            continue
        region_id = str(region.get("region_id", "")).upper()
        if region_id in REGION_IDS:
            regions[region_id] = {
                "region_id": region_id,
                "fill_percent": float(region.get("fill_percent", 0) or 0),
                "available_mass_tonnes": float(region.get("available_mass_tonnes", 0) or 0),
            }
    return regions


def best_available_region(challenge1_state: dict[str, Any]) -> str:
    regions = regions_by_id(challenge1_state)
    if not regions:
        return "CENTER"
    return max(regions.values(), key=lambda item: item["available_mass_tonnes"])["region_id"]


def recommend_unloading_region(
    cv: float,
    weight_tonnes: float,
    challenge1_state: dict[str, Any],
) -> dict[str, Any]:
    preferred = preferred_region_for_cv(cv)
    regions = regions_by_id(challenge1_state)
    preferred_region = regions.get(preferred)
    fallback_used = False
    capacity_warning = None

    if (
        preferred_region
        and preferred_region["fill_percent"] < 85
        and preferred_region["available_mass_tonnes"] >= weight_tonnes
    ):
        selected = preferred
        reason = (
            f"CV {cv:g} MJ/kg material is best tracked in the {preferred} operational region, "
            "which has available capacity."
        )
    else:
        fallback_used = True
        selected = best_available_region(challenge1_state)
        reason = (
            f"The preferred {preferred} operational region is nearly full or short on capacity. "
            f"WasteIQ recommends {selected}, the region with the highest available mass, and keeps the layer tracked virtually."
        )

    selected_region = regions.get(selected, {"fill_percent": 100, "available_mass_tonnes": 0})
    if not regions or all(region["fill_percent"] >= 85 for region in regions.values()) or selected_region["available_mass_tonnes"] < weight_tonnes:
        capacity_warning = "Limited bunker capacity — operator review required."

    return {
        "preferred_region": preferred,
        "recommended_unloading_region": selected,
        "fallback_used": fallback_used,
        "reason": reason,
        "capacity_warning": capacity_warning,
        "region_fill_percent": round(float(selected_region.get("fill_percent", 0) or 0), 1),
        "region_available_mass_tonnes": round(float(selected_region.get("available_mass_tonnes", 0) or 0), 2),
    }
