from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any

from app.config import settings
from app.core.cv_calculator import calculate_weighted_cv, risk_status, round_cv
from app.data.waste_code_mapping import (
    WASTE_CV,
    capacity_for_waste_code,
    known_waste_codes,
    name_for_waste_code,
)


ZONE_ORDER = ("LOW", "MEDIUM", "HIGH")

ZONE_META: dict[str, dict[str, str]] = {
    "LOW": {
        "zone_name": "Low CV Cluster",
        "risk_if_overused": "Can weaken combustion and reduce energy output if overused.",
    },
    "MEDIUM": {
        "zone_name": "Medium / Desired CV Cluster",
        "risk_if_overused": "Primary stabilizing cluster; preserve enough mass for steady operation.",
    },
    "HIGH": {
        "zone_name": "High CV Cluster",
        "risk_if_overused": "High-value correction reserve; exhausting it early reduces future control.",
    },
}


def _timestamp_sort_key(timestamp: str) -> datetime:
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min


def assign_zone_id(cv: float) -> str:
    if cv < 9:
        return "LOW"
    if cv <= 12:
        return "MEDIUM"
    return "HIGH"


def add_zone_to_shipments(shipments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **row,
            "assigned_zone": assign_zone_id(float(row.get("cv", 0))),
            "assigned_bunker": row.get("waste_code", "UNKNOWN"),
        }
        for row in shipments
    ]


def _recent_arrival_rates(shipments: list[dict[str, Any]], horizon_hours: float = 2.0) -> dict[str, float]:
    if not shipments:
        return {}

    latest = max(_timestamp_sort_key(row["timestamp"]) for row in shipments)
    window_start = latest - timedelta(hours=horizon_hours)
    recent_totals: dict[str, float] = defaultdict(float)

    for row in shipments:
        timestamp = _timestamp_sort_key(row["timestamp"])
        if timestamp >= window_start:
            recent_totals[row["waste_code"]] += float(row["weight_tonnes"])

    return {code: tonnes / horizon_hours for code, tonnes in recent_totals.items()}


def build_bunker_cells(shipments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    totals: dict[str, dict[str, Any]] = defaultdict(lambda: {"weight_tonnes": 0.0, "energy_mj": 0.0, "shipment_count": 0})

    for row in shipments:
        code = row["waste_code"]
        totals[code]["weight_tonnes"] += float(row["weight_tonnes"])
        totals[code]["energy_mj"] += float(row["energy_mj"])
        totals[code]["shipment_count"] += 1

    codes = list(known_waste_codes().keys())
    if "UNKNOWN" in totals:
        codes.append("UNKNOWN")

    arrival_rates = _recent_arrival_rates(shipments)
    cells: list[dict[str, Any]] = []
    for code in codes:
        mapped = WASTE_CV.get(code, WASTE_CV["UNKNOWN"])
        cv = float(mapped["cv"])
        mass = float(totals[code]["weight_tonnes"])
        capacity = capacity_for_waste_code(code)
        fill_pct = (mass / capacity) * 100 if capacity else 0.0
        free_capacity = max(capacity - mass, 0.0)
        recent_rate = arrival_rates.get(code, 0.0)
        projected_incoming = recent_rate * settings.default_duration_hours
        projected_fill_without_feeding = ((mass + projected_incoming) / capacity) * 100 if capacity else 0.0

        if mass <= 0:
            status = "EMPTY"
        elif fill_pct >= 100:
            status = "OVER_CAPACITY"
        elif fill_pct >= 85:
            status = "NEAR_CAPACITY"
        elif fill_pct <= 10:
            status = "LOW_STOCK"
        else:
            status = "AVAILABLE"

        if status in {"OVER_CAPACITY", "NEAR_CAPACITY"}:
            storage_action = "Prioritize this bunker in the feed plan to create space for incoming trucks."
        elif projected_fill_without_feeding >= 85:
            storage_action = "Incoming trend could create space pressure; monitor this bunker closely."
        elif mass <= 0:
            storage_action = "No active stock; route matching future trucks here when they arrive."
        else:
            storage_action = "Storage level is operationally comfortable."

        cells.append(
            {
                "bunker_id": code,
                "waste_code": code,
                "waste_name": name_for_waste_code(code),
                "cv": round_cv(cv),
                "cv_class": assign_zone_id(cv),
                "available_mass_tonnes": round(mass, 2),
                "capacity_tonnes": round(capacity, 2),
                "fill_pct": round(fill_pct, 1),
                "free_capacity_tonnes": round(free_capacity, 2),
                "status": status,
                "shipment_count": int(totals[code]["shipment_count"]),
                "recent_arrival_rate_tonnes_per_hour": round(recent_rate, 2),
                "projected_incoming_2h_tonnes": round(projected_incoming, 2),
                "projected_fill_without_feeding_pct": round(projected_fill_without_feeding, 1),
                "storage_action": storage_action,
                "target_fit_error": round(abs(cv - settings.target_cv), 2),
            }
        )

    return sorted(cells, key=lambda cell: (cell["status"] == "EMPTY", -cell["available_mass_tonnes"], cell["waste_code"]))


def build_waste_distribution(shipments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    totals: dict[str, dict[str, Any]] = defaultdict(lambda: {"weight_kg": 0.0, "waste_name": "", "cv": 0.0})

    for row in shipments:
        code = row["waste_code"]
        totals[code]["weight_kg"] += float(row["weight_kg"])
        totals[code]["waste_name"] = row["waste_name"]
        totals[code]["cv"] = row["cv"]

    total_weight = sum(item["weight_kg"] for item in totals.values()) or 1.0
    distribution = []
    for code, item in totals.items():
        distribution.append(
            {
                "waste_code": code,
                "waste_name": item["waste_name"],
                "cv": item["cv"],
                "weight_kg": round(item["weight_kg"], 2),
                "weight_tonnes": round(item["weight_kg"] / 1000, 2),
                "percentage": round((item["weight_kg"] / total_weight) * 100, 1),
            }
        )

    return sorted(distribution, key=lambda item: item["weight_kg"], reverse=True)


def build_zones(shipments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    zoned_shipments = add_zone_to_shipments(shipments)
    total_mass_kg = sum(float(row["weight_kg"]) for row in zoned_shipments)
    zones: list[dict[str, Any]] = []

    for zone_id in ZONE_ORDER:
        zone_rows = [row for row in zoned_shipments if row["assigned_zone"] == zone_id]
        zone_mass_kg = sum(float(row["weight_kg"]) for row in zone_rows)
        waste_codes = sorted({row["waste_code"] for row in zone_rows})
        avg_cv = calculate_weighted_cv(zone_rows) if zone_rows else 0.0

        zones.append(
            {
                "zone_id": zone_id,
                "zone_name": ZONE_META[zone_id]["zone_name"],
                "avg_cv": round_cv(avg_cv),
                "available_mass_tonnes": round(zone_mass_kg / 1000, 2),
                "percentage_of_total_mass": round((zone_mass_kg / total_mass_kg) * 100, 1) if total_mass_kg else 0,
                "waste_codes_inside": waste_codes,
                "risk_if_overused": ZONE_META[zone_id]["risk_if_overused"],
                "status": "AVAILABLE" if zone_mass_kg > 0 else "DISABLED",
            }
        )

    return zones


def _storage_summary(cells: list[dict[str, Any]]) -> dict[str, Any]:
    total_capacity = sum(float(cell["capacity_tonnes"]) for cell in cells)
    total_mass = sum(float(cell["available_mass_tonnes"]) for cell in cells)
    pressure_cells = [cell for cell in cells if cell["status"] in {"NEAR_CAPACITY", "OVER_CAPACITY"}]
    projected_pressure_cells = [cell for cell in cells if float(cell["projected_fill_without_feeding_pct"]) >= 85]
    return {
        "total_capacity_tonnes": round(total_capacity, 2),
        "used_capacity_tonnes": round(total_mass, 2),
        "free_capacity_tonnes": round(max(total_capacity - total_mass, 0), 2),
        "average_fill_pct": round((total_mass / total_capacity) * 100, 1) if total_capacity else 0,
        "pressure_bunker_count": len(pressure_cells),
        "projected_pressure_bunker_count": len(projected_pressure_cells),
        "pressure_bunkers": [cell["waste_code"] for cell in pressure_cells],
        "capacity_model_note": "Capacity is modeled in tonnes as a volume proxy because density is not part of this prototype.",
    }


def build_dashboard_payload(shipments: list[dict[str, Any]], source_meta: dict[str, Any] | None = None) -> dict[str, Any]:
    source_meta = source_meta or {"demo_mode": False, "message": "Loaded shipment data."}
    zoned_shipments = add_zone_to_shipments(shipments)
    zones = build_zones(zoned_shipments)
    bunker_cells = build_bunker_cells(zoned_shipments)
    total_weight_kg = sum(float(row["weight_kg"]) for row in zoned_shipments)
    current_cv = calculate_weighted_cv(zoned_shipments)
    latest_shipments = sorted(zoned_shipments, key=lambda item: item["timestamp"], reverse=True)[:10]
    zone_masses = {zone["zone_id"]: zone["available_mass_tonnes"] for zone in zones}
    dominant_zone = max(zone_masses, key=zone_masses.get) if zone_masses else "NONE"
    waste_counts = Counter(row["waste_code"] for row in zoned_shipments)
    dominant_waste_code = waste_counts.most_common(1)[0][0] if waste_counts else "NONE"

    return {
        "demo_mode": bool(source_meta.get("demo_mode", False)),
        "data_source_message": source_meta.get("message", ""),
        "target_cv": settings.target_cv,
        "target_cv_min": settings.target_cv_min,
        "target_cv_max": settings.target_cv_max,
        "safe_min_cv": settings.safe_cv_min,
        "safe_max_cv": settings.safe_cv_max,
        "current_cv": round_cv(current_cv),
        "total_mass_tonnes": round(total_weight_kg / 1000, 2),
        "shipment_count": len(zoned_shipments),
        "dominant_zone": dominant_zone,
        "dominant_waste_code": dominant_waste_code,
        "first_timestamp": zoned_shipments[0]["timestamp"] if zoned_shipments else None,
        "latest_timestamp": zoned_shipments[-1]["timestamp"] if zoned_shipments else None,
        "risk_status": risk_status(current_cv),
        "zones": zones,
        "bunker_cells": bunker_cells,
        "storage_summary": _storage_summary(bunker_cells),
        "waste_distribution": build_waste_distribution(zoned_shipments),
        "latest_shipments": latest_shipments,
    }
