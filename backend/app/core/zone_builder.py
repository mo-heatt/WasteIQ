from __future__ import annotations

from collections import Counter
from typing import Any

from app.core.cv_calculator import calculate_weighted_cv, risk_status, round_cv


ZONE_ORDER = ("LOW", "MEDIUM", "HIGH")
REGION_TO_ZONE = {"LEFT": "LOW", "CENTER": "MEDIUM", "RIGHT": "HIGH"}
FALLBACK_ZONE_CV = {"LOW": 8.5, "MEDIUM": 10.0, "HIGH": 14.5}

ZONE_META: dict[str, dict[str, str]] = {
    "LOW": {
        "zone_name": "LOW CV Zone",
        "risk_if_overused": "Overusing low-CV material can weaken combustion and reduce energy output.",
    },
    "MEDIUM": {
        "zone_name": "MEDIUM CV Zone",
        "risk_if_overused": "Medium-CV material is the stabilizing buffer for normal operation.",
    },
    "HIGH": {
        "zone_name": "HIGH CV Zone",
        "risk_if_overused": "High-CV material is valuable correction reserve; exhausting it early reduces future control.",
    },
}


def assign_cv_zone(cv: float) -> str:
    if cv < 9:
        return "LOW"
    if cv <= 12:
        return "MEDIUM"
    return "HIGH"


def add_virtual_zone_to_shipments(shipments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **row,
            "assigned_cv_zone": row.get("assigned_cv_zone") or assign_cv_zone(float(row.get("cv", 0))),
            "assigned_zone": row.get("assigned_zone") or row.get("assigned_cv_zone") or assign_cv_zone(float(row.get("cv", 0))),
        }
        for row in shipments
    ]


def _challenge_regions_by_zone(challenge1_state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for region in challenge1_state.get("regions", []):
        region_id = str(region.get("region_id", "")).upper()
        zone_id = REGION_TO_ZONE.get(region_id)
        if zone_id:
            mapped[zone_id] = region
    return mapped


def build_virtual_zones(shipments: list[dict[str, Any]], challenge1_state: dict[str, Any]) -> list[dict[str, Any]]:
    zoned_shipments = add_virtual_zone_to_shipments(shipments)
    regions_by_zone = _challenge_regions_by_zone(challenge1_state)
    total_available = sum(float(region.get("available_mass_tonnes", 0) or 0) for region in regions_by_zone.values())
    if total_available <= 0:
        total_available = sum(float(row.get("weight_tonnes", 0) or 0) for row in zoned_shipments)

    zones: list[dict[str, Any]] = []
    for zone_id in ZONE_ORDER:
        zone_rows = [row for row in zoned_shipments if row["assigned_cv_zone"] == zone_id]
        shipment_mass = sum(float(row["weight_tonnes"]) for row in zone_rows)
        region = regions_by_zone.get(zone_id, {})
        available_mass = float(region.get("available_mass_tonnes", shipment_mass) or 0)
        fill_percent = float(region.get("fill_percent", 0) or 0)
        region_id = region.get("region_id")
        avg_cv = calculate_weighted_cv(zone_rows) if zone_rows else FALLBACK_ZONE_CV[zone_id]
        waste_codes = sorted({row["waste_code"] for row in zone_rows})

        if available_mass <= 0:
            status = "NO_AVAILABLE_MASS"
        elif fill_percent >= 85:
            status = "HIGH_FILL"
        elif available_mass < 10:
            status = "LOW_STOCK"
        else:
            status = "AVAILABLE"

        if zone_rows:
            cv_note = "CV average calculated from shipment waste codes."
        else:
            cv_note = f"No recent shipment rows classified as {zone_id}; using demo fallback CV {FALLBACK_ZONE_CV[zone_id]} MJ/kg."

        source_note = (
            f"{region_id or 'Unmapped'} Challenge 1 region mapped to {zone_id}. "
            f"{cv_note} This mapping is software-defined and can be replaced by Challenge 1 classification output."
        )

        zones.append(
            {
                "zone_id": zone_id,
                "zone_name": ZONE_META[zone_id]["zone_name"],
                "avg_cv": round_cv(avg_cv),
                "available_mass_tonnes": round(available_mass, 2),
                "shipment_mass_tonnes": round(shipment_mass, 2),
                "fill_percent": round(fill_percent, 1),
                "percentage_of_total_mass": round((available_mass / total_available) * 100, 1) if total_available else 0,
                "waste_codes_inside": waste_codes,
                "status": status,
                "risk_if_overused": ZONE_META[zone_id]["risk_if_overused"],
                "source_note": source_note,
                "region_id": region_id,
            }
        )

    return zones


def build_zone_distribution(shipments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    zoned_shipments = add_virtual_zone_to_shipments(shipments)
    totals: dict[str, float] = {zone_id: 0.0 for zone_id in ZONE_ORDER}
    for row in zoned_shipments:
        totals[row["assigned_cv_zone"]] += float(row["weight_tonnes"])
    total = sum(totals.values()) or 1.0
    return [
        {"zone_id": zone_id, "weight_tonnes": round(value, 2), "percentage": round((value / total) * 100, 1)}
        for zone_id, value in totals.items()
    ]


def current_bunker_summary(shipments: list[dict[str, Any]]) -> dict[str, Any]:
    zoned_shipments = add_virtual_zone_to_shipments(shipments)
    current_cv = calculate_weighted_cv(zoned_shipments)
    total_mass = sum(float(row["weight_tonnes"]) for row in zoned_shipments)
    waste_counts = Counter(row["waste_code"] for row in zoned_shipments)
    return {
        "current_cv": round_cv(current_cv),
        "risk_status": risk_status(current_cv),
        "total_mass_tonnes": round(total_mass, 2),
        "shipment_count": len(zoned_shipments),
        "first_timestamp": zoned_shipments[0]["timestamp"] if zoned_shipments else None,
        "latest_timestamp": zoned_shipments[-1]["timestamp"] if zoned_shipments else None,
        "dominant_waste_code": waste_counts.most_common(1)[0][0] if waste_counts else "NONE",
        "latest_shipments": sorted(zoned_shipments, key=lambda item: item["timestamp"], reverse=True)[:10],
    }
