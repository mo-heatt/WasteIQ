from __future__ import annotations

from typing import Iterable


def calculate_weighted_cv(shipments: Iterable[dict]) -> float:
    rows = list(shipments)
    total_weight = sum(float(row.get("weight_kg", 0)) for row in rows)
    if total_weight <= 0:
        return 0.0

    total_energy = sum(float(row.get("energy_mj", 0)) for row in rows)
    return total_energy / total_weight


def risk_status(cv: float) -> str:
    if cv < 8:
        return "LOW_CV_CRITICAL"
    if 8 <= cv < 9:
        return "LOW_CV_WARNING"
    if 9 <= cv <= 11:
        return "STABLE"
    if 11 < cv <= 12:
        return "HIGH_CV_WARNING"
    return "HIGH_CV_CRITICAL"


def round_cv(value: float) -> float:
    return round(value, 2)
