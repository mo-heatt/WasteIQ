from __future__ import annotations

from statistics import pstdev
from typing import Any

from app.config import settings
from app.core.mix_simulator import simulate_mix


def _allocation_units(count: int, total_units: int = 20) -> list[list[int]]:
    if count == 1:
        return [[total_units]]

    allocations: list[list[int]] = []
    for units in range(total_units + 1):
        for rest in _allocation_units(count - 1, total_units - units):
            allocations.append([units, *rest])
    return allocations


def _candidate_cells(bunker_cells: list[dict[str, Any]], max_cells: int = 7) -> list[dict[str, Any]]:
    active = [cell for cell in bunker_cells if float(cell["available_mass_tonnes"]) > 0]
    if len(active) <= max_cells:
        return active

    # Keep a bounded search while preserving operationally important candidates:
    # near-target bunkers, storage-pressure bunkers, and high-mass bunkers.
    selected: dict[str, dict[str, Any]] = {}
    for cell in sorted(active, key=lambda item: item["target_fit_error"])[:3]:
        selected[cell["waste_code"]] = cell
    for cell in sorted(active, key=lambda item: item["projected_fill_without_feeding_pct"], reverse=True)[:3]:
        selected[cell["waste_code"]] = cell
    for cell in sorted(active, key=lambda item: item["available_mass_tonnes"], reverse=True):
        selected[cell["waste_code"]] = cell
        if len(selected) >= max_cells:
            break
    return list(selected.values())


def _score_candidate(simulation: dict[str, Any], cells_by_code: dict[str, dict[str, Any]]) -> tuple[float, dict[str, float]]:
    target_error = float(simulation["target_error"])
    target_band_error = float(simulation["target_band_error"])
    max_exhaustion_risk = max(float(value) for value in simulation["exhaustion_risk_by_bunker"].values())
    shares = [float(value) / 100 for value in simulation["input_mix_percentages"].values()]
    imbalance_penalty = pstdev(shares) + max(0.0, max(shares) - 0.55)
    unsafe_penalty = 200.0 if not simulation["is_cv_safe"] else 0.0
    target_band_penalty = 60.0 * target_band_error

    high_value_preservation_penalty = 0.0
    storage_pressure_penalty = 0.0
    projected_overflow_penalty = 0.0
    for code, pct in simulation["input_mix_percentages"].items():
        cell = cells_by_code[code]
        share = pct / 100
        fill = min(float(cell["fill_pct"]) / 100, 1.2)
        cv = float(cell["cv"])
        if cv > settings.safe_cv_max:
            high_value_preservation_penalty += share * 4.0
        storage_pressure_penalty += share * (1.0 - min(fill, 1.0))

    for projected_fill in simulation["projected_fill_after_2h"].values():
        if projected_fill > 95:
            projected_overflow_penalty += (projected_fill - 95) * 0.5

    score = (
        8 * target_error
        + target_band_penalty
        + 4 * max_exhaustion_risk
        + 3 * imbalance_penalty
        + high_value_preservation_penalty
        + 2 * storage_pressure_penalty
        + projected_overflow_penalty
        + unsafe_penalty
    )
    metrics = {
        "target_error": round(target_error, 3),
        "target_band_error": round(target_band_error, 3),
        "max_exhaustion_risk": round(max_exhaustion_risk, 3),
        "imbalance_penalty": round(imbalance_penalty, 3),
        "unsafe_penalty": round(unsafe_penalty, 3),
        "high_value_preservation_penalty": round(high_value_preservation_penalty, 3),
        "storage_pressure_penalty": round(storage_pressure_penalty, 3),
        "projected_overflow_penalty": round(projected_overflow_penalty, 3),
    }
    return score, metrics


def optimize_mix(
    bunker_cells: list[dict[str, Any]],
    feed_rate_tonnes_per_hour: float = 10,
    duration_hours: float = 2,
) -> dict[str, Any]:
    candidates = _candidate_cells(bunker_cells)
    cells_by_code = {cell["waste_code"]: cell for cell in candidates}
    best: dict[str, Any] | None = None

    if not candidates:
        return {
            "recommended_mix_percentages": {},
            "all_bunker_percentages": {cell["waste_code"]: 0 for cell in bunker_cells},
            "expected_cv": 0,
            "expected_cv_after_2h": 0,
            "score": 999,
            "explanation_reason": "No available bunker mass was found for optimization.",
            "why_not_overuse_one_bunker": "No feasible plan can be created from empty bunkers.",
            "storage_management_reason": "Route incoming trucks into empty bunkers before feeding.",
            "is_safe": False,
            "is_within_target_band": False,
            "is_feasible": False,
        }

    for allocation in _allocation_units(len(candidates)):
        mix = {
            cell["waste_code"]: units * 5.0
            for cell, units in zip(candidates, allocation)
            if units > 0
        }
        simulation = simulate_mix(bunker_cells, mix, feed_rate_tonnes_per_hour, duration_hours)
        if not simulation["is_feasible"]:
            continue

        score, metrics = _score_candidate(simulation, cells_by_code)
        all_percentages = {cell["waste_code"]: 0.0 for cell in bunker_cells}
        all_percentages.update(simulation["input_mix_percentages"])
        candidate = {
            "recommended_mix_percentages": simulation["input_mix_percentages"],
            "all_bunker_percentages": all_percentages,
            "expected_cv": simulation["blended_cv"],
            "expected_cv_after_2h": simulation["blended_cv"],
            "consumed_by_bunker": simulation["consumed_by_bunker"],
            "remaining_by_bunker": simulation["remaining_by_bunker"],
            "projected_fill_after_2h": simulation["projected_fill_after_2h"],
            "exhaustion_risk_by_bunker": simulation["exhaustion_risk_by_bunker"],
            "consumed_by_zone": simulation["consumed_by_zone"],
            "score": round(score, 3),
            "score_metrics": metrics,
            "feed_rate_tonnes_per_hour": feed_rate_tonnes_per_hour,
            "duration_hours": duration_hours,
            "is_safe": simulation["is_cv_safe"],
            "is_within_target_band": simulation["is_target_band"],
            "is_feasible": simulation["is_feasible"],
        }

        if best is None or candidate["score"] < best["score"]:
            best = candidate

    if best is None:
        return {
            "recommended_mix_percentages": {},
            "all_bunker_percentages": {cell["waste_code"]: 0 for cell in bunker_cells},
            "expected_cv": 0,
            "expected_cv_after_2h": 0,
            "score": 999,
            "explanation_reason": "No feasible mix was found for the requested real-time feed plan.",
            "why_not_overuse_one_bunker": "WasteIQ will not recommend consuming more mass than a bunker contains.",
            "storage_management_reason": "Reduce feed duration or wait for more incoming trucks.",
            "is_safe": False,
            "is_within_target_band": False,
            "is_feasible": False,
        }

    mix = best["recommended_mix_percentages"]
    primary_code = max(mix, key=mix.get)
    high_cv_used = [
        code for code, pct in mix.items()
        if pct > 0 and float(next(cell for cell in bunker_cells if cell["waste_code"] == code)["cv"]) > settings.safe_cv_max
    ]
    storage_pressure = [
        cell["waste_code"]
        for cell in bunker_cells
        if cell["status"] in {"NEAR_CAPACITY", "OVER_CAPACITY"} or float(cell["projected_fill_without_feeding_pct"]) >= 85
    ]

    best["explanation_reason"] = (
        f"The optimizer selected a waste-type bunker mix with expected CV {best['expected_cv']} MJ/kg, "
        f"aiming for the preferred {settings.target_cv_min}-{settings.target_cv_max} MJ/kg band."
    )
    best["why_not_overuse_one_bunker"] = (
        f"The largest feed share is {mix[primary_code]}% from bunker {primary_code}. "
        f"The score penalizes high exhaustion risk and one-bunker dependency."
    )
    best["storage_management_reason"] = (
        "The plan consumes from high-fill bunkers where useful while preserving scarce high-CV reserve. "
        f"Storage-pressure bunkers watched over the next 2 hours: {', '.join(storage_pressure) if storage_pressure else 'none'}."
    )
    best["high_value_preservation_reason"] = (
        "High-CV bunkers are used only when needed to hit the target band."
        if high_cv_used
        else "High-CV bunkers are preserved because medium-CV material can meet the target band."
    )
    return best
