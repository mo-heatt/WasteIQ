from __future__ import annotations

from statistics import pstdev
from typing import Any

from app.config import settings
from app.core.cv_calculator import round_cv
from app.core.region_mapper import REGION_IDS


def _region_map(regions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(region["region_id"]).upper(): region for region in regions}


def _validate_mix(percentages: dict[str, float]) -> list[str]:
    warnings: list[str] = []
    total = sum(float(percentages.get(region_id, 0) or 0) for region_id in REGION_IDS)
    if abs(total - 100) > 0.001:
        warnings.append("LEFT, CENTER and RIGHT percentages must sum to 100%.")
    return warnings


def build_region_crane_plan(percentages: dict[str, float], total_feed_mass_tonnes: float) -> dict[str, Any]:
    target_tonnes = {
        region_id: round(total_feed_mass_tonnes * (float(percentages.get(region_id, 0) or 0) / 100), 2)
        for region_id in REGION_IDS
    }
    instruction = (
        f"Feed {target_tonnes['LEFT']:.1f}t from LEFT, {target_tonnes['CENTER']:.1f}t from CENTER, "
        f"and {target_tonnes['RIGHT']:.1f}t from RIGHT over the next {settings.default_duration_hours:g} hours."
    )
    return {
        "target_tonnes_by_region": target_tonnes,
        "operator_instruction": instruction,
        "planning_note": (
            "Region percentages are translated into tonnes for the crane operator. WasteIQ is decision support, "
            "not autonomous crane control."
        ),
    }


def simulate_region_mix(
    regions: list[dict[str, Any]],
    left_pct: float,
    center_pct: float,
    right_pct: float,
    feed_rate_tonnes_per_hour: float = 10,
    duration_hours: float = 2,
) -> dict[str, Any]:
    percentages = {"LEFT": float(left_pct), "CENTER": float(center_pct), "RIGHT": float(right_pct)}
    warnings = _validate_mix(percentages)
    total_feed_mass = max(float(feed_rate_tonnes_per_hour), 0.0) * max(float(duration_hours), 0.0)
    regions_by_id = _region_map(regions)

    blended_cv = 0.0
    consumed_by_region: dict[str, float] = {}
    remaining_by_region: dict[str, float] = {}
    exhaustion_risk_by_region: dict[str, float] = {}
    composition_used: list[dict[str, Any]] = []

    for region_id in REGION_IDS:
        region = regions_by_id.get(region_id, {})
        share = percentages[region_id] / 100
        avg_cv = float(region.get("average_cv", region.get("avg_cv", 0)) or 0)
        available = float(region.get("available_mass_tonnes", 0) or 0)
        consumed = total_feed_mass * share
        blended_cv += share * avg_cv

        if percentages[region_id] > 0 and available <= 0:
            warnings.append(f"{region_id} region has no available mass.")
        if consumed > available + 0.001:
            warnings.append(f"{region_id} region does not have enough mass for this feed plan.")

        consumed_by_region[region_id] = round(consumed, 2)
        remaining_by_region[region_id] = round(max(available - consumed, 0.0), 2)
        exhaustion_risk_by_region[region_id] = round((consumed / available) if available > 0 else (1.0 if consumed > 0 else 0.0), 3)
        composition_used.append(
            {
                "region_id": region_id,
                "average_cv": round_cv(avg_cv),
                "dominant_waste_code": region.get("dominant_waste_code", "UNKNOWN"),
                "waste_layer_composition": region.get("waste_layer_composition", []),
            }
        )

    is_cv_safe = settings.safe_cv_min <= blended_cv <= settings.safe_cv_max
    if not is_cv_safe:
        warnings.append("Blended CV is outside the safe operating band.")

    return {
        "input_mix_percentages": {region_id: round(percentages[region_id], 1) for region_id in REGION_IDS},
        "blended_cv": round_cv(blended_cv),
        "is_cv_safe": is_cv_safe,
        "target_error": round(abs(blended_cv - settings.target_cv), 2),
        "total_feed_mass_tonnes": round(total_feed_mass, 2),
        "feed_rate_tonnes_per_hour": round(float(feed_rate_tonnes_per_hour), 2),
        "duration_hours": round(float(duration_hours), 2),
        "consumed_by_region": consumed_by_region,
        "remaining_by_region": remaining_by_region,
        "exhaustion_risk_by_region": exhaustion_risk_by_region,
        "max_exhaustion_risk": round(max(exhaustion_risk_by_region.values()) if exhaustion_risk_by_region else 0.0, 3),
        "is_feasible": len([warning for warning in warnings if "safe operating band" not in warning]) == 0,
        "warnings": warnings,
        "region_composition_used": composition_used,
        "crane_plan": build_region_crane_plan(percentages, total_feed_mass),
    }


def score_region_simulation(simulation: dict[str, Any]) -> tuple[float, dict[str, float]]:
    shares = [float(value) / 100 for value in simulation["input_mix_percentages"].values()]
    max_exhaustion = float(simulation["max_exhaustion_risk"])
    imbalance_penalty = pstdev(shares) + max(0.0, max(shares) - 0.7)
    unsafe_penalty = 100.0 if not simulation["is_cv_safe"] else 0.0
    score = (
        5 * float(simulation["target_error"])
        + 3 * max_exhaustion
        + 2 * imbalance_penalty
        + unsafe_penalty
    )
    return round(score, 3), {
        "target_error": round(float(simulation["target_error"]), 3),
        "max_exhaustion_risk": round(max_exhaustion, 3),
        "imbalance_penalty": round(imbalance_penalty, 3),
        "unsafe_penalty": round(unsafe_penalty, 3),
    }


def optimize_region_mix(
    regions: list[dict[str, Any]],
    feed_rate_tonnes_per_hour: float = 10,
    duration_hours: float = 2,
) -> dict[str, Any]:
    best: dict[str, Any] | None = None
    for left in range(0, 101, 5):
        for center in range(0, 101 - left, 5):
            right = 100 - left - center
            simulation = simulate_region_mix(regions, left, center, right, feed_rate_tonnes_per_hour, duration_hours)
            if not simulation["is_feasible"]:
                continue
            score, score_metrics = score_region_simulation(simulation)
            candidate = {
                "recommended_region_mix": simulation["input_mix_percentages"],
                "mix_percentages": simulation["input_mix_percentages"],
                "simulation": simulation,
                "expected_cv": simulation["blended_cv"],
                "duration_hours": simulation["duration_hours"],
                "feed_rate_tonnes_per_hour": simulation["feed_rate_tonnes_per_hour"],
                "total_feed_mass_tonnes": simulation["total_feed_mass_tonnes"],
                "consumed_by_region": simulation["consumed_by_region"],
                "remaining_by_region": simulation["remaining_by_region"],
                "exhaustion_risk_by_region": simulation["exhaustion_risk_by_region"],
                "score": score,
                "score_metrics": score_metrics,
                "is_safe": simulation["is_cv_safe"],
                "is_feasible": simulation["is_feasible"],
            }
            if best is None or candidate["score"] < best["score"]:
                best = candidate

    if best is None:
        simulation = simulate_region_mix(regions, 33, 34, 33, feed_rate_tonnes_per_hour, duration_hours)
        best = {
            "recommended_region_mix": simulation["input_mix_percentages"],
            "mix_percentages": simulation["input_mix_percentages"],
            "simulation": simulation,
            "expected_cv": simulation["blended_cv"],
            "duration_hours": simulation["duration_hours"],
            "feed_rate_tonnes_per_hour": simulation["feed_rate_tonnes_per_hour"],
            "total_feed_mass_tonnes": simulation["total_feed_mass_tonnes"],
            "consumed_by_region": simulation["consumed_by_region"],
            "remaining_by_region": simulation["remaining_by_region"],
            "exhaustion_risk_by_region": simulation["exhaustion_risk_by_region"],
            "score": 999.0,
            "score_metrics": {},
            "is_safe": simulation["is_cv_safe"],
            "is_feasible": False,
        }

    mix = best["recommended_region_mix"]
    primary_region = max(mix, key=mix.get)
    tonnes = best["simulation"]["crane_plan"]["target_tonnes_by_region"]
    best["why_this_mix_is_best"] = (
        f"The selected region recipe reaches {best['expected_cv']} MJ/kg with target error "
        f"{best['simulation']['target_error']} while keeping max region depletion at "
        f"{round(best['simulation']['max_exhaustion_risk'] * 100)}%."
    )
    best["why_not_overuse_one_region"] = (
        f"The largest share is {mix[primary_region]:.0f}% from {primary_region}; the score penalizes one-region dominance "
        "and depletion of limited bunker capacity."
    )
    best["operator_instruction"] = (
        f"Feed {tonnes['LEFT']:.1f}t from LEFT, {tonnes['CENTER']:.1f}t from CENTER, "
        f"and {tonnes['RIGHT']:.1f}t from RIGHT over the next {best['duration_hours']:g} hours."
    )
    return best


def default_naive_region_mix(regions: list[dict[str, Any]]) -> dict[str, Any]:
    simulation = simulate_region_mix(regions, 33, 34, 33, settings.default_feed_rate_tonnes_per_hour, settings.default_duration_hours)
    score, score_metrics = score_region_simulation(simulation)
    return {
        "recommended_region_mix": simulation["input_mix_percentages"],
        "mix_percentages": simulation["input_mix_percentages"],
        "simulation": simulation,
        "expected_cv": simulation["blended_cv"],
        "consumed_by_region": simulation["consumed_by_region"],
        "remaining_by_region": simulation["remaining_by_region"],
        "exhaustion_risk_by_region": simulation["exhaustion_risk_by_region"],
        "score": score,
        "score_metrics": score_metrics,
        "is_safe": simulation["is_cv_safe"],
        "is_feasible": simulation["is_feasible"],
    }
