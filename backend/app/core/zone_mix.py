from __future__ import annotations

from statistics import pstdev
from typing import Any

from app.config import settings
from app.core.cv_calculator import round_cv


ZONE_IDS = ("LOW", "MEDIUM", "HIGH")


def _zone_map(zones: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {zone["zone_id"]: zone for zone in zones}


def _target_error(cv: float) -> float:
    return abs(cv - settings.target_cv)


def _mix_from_payload(low_pct: float, medium_pct: float, high_pct: float) -> dict[str, float]:
    return {"LOW": float(low_pct), "MEDIUM": float(medium_pct), "HIGH": float(high_pct)}


def _allocate_integer_grabs(target_tonnes: dict[str, float], grab_size_tonnes: float) -> dict[str, int]:
    total_tonnes = sum(target_tonnes.values())
    if total_tonnes <= 0 or grab_size_tonnes <= 0:
        return {zone_id: 0 for zone_id in ZONE_IDS}

    total_grabs = max(1, round(total_tonnes / grab_size_tonnes))
    exact_grabs = {zone_id: target_tonnes[zone_id] / grab_size_tonnes for zone_id in ZONE_IDS}
    grabs = {zone_id: int(exact_grabs[zone_id]) for zone_id in ZONE_IDS}
    remaining = total_grabs - sum(grabs.values())

    remainders = sorted(
        ZONE_IDS,
        key=lambda zone_id: (exact_grabs[zone_id] - grabs[zone_id], target_tonnes[zone_id]),
        reverse=True,
    )
    for zone_id in remainders[: max(remaining, 0)]:
        grabs[zone_id] += 1

    return grabs


def _interleaved_sequence(grab_counts: dict[str, int]) -> list[str]:
    total = sum(grab_counts.values())
    if total <= 0:
        return []

    used = {zone_id: 0 for zone_id in ZONE_IDS}
    sequence: list[str] = []
    for slot in range(1, total + 1):
        best_zone = max(
            ZONE_IDS,
            key=lambda zone_id: (
                (grab_counts[zone_id] * slot / total) - used[zone_id],
                grab_counts[zone_id],
            ),
        )
        if used[best_zone] >= grab_counts[best_zone]:
            available = [zone_id for zone_id in ZONE_IDS if used[zone_id] < grab_counts[zone_id]]
            if not available:
                break
            best_zone = max(available, key=lambda zone_id: grab_counts[zone_id] - used[zone_id])
        used[best_zone] += 1
        sequence.append(best_zone)
    return sequence


def build_crane_plan(
    percentages: dict[str, float],
    total_feed_mass_tonnes: float,
    grab_size_tonnes: float | None = None,
) -> dict[str, Any]:
    grab_size = float(grab_size_tonnes or settings.default_crane_grab_tonnes)
    target_tonnes = {
        zone_id: round(total_feed_mass_tonnes * (float(percentages.get(zone_id, 0.0)) / 100), 2)
        for zone_id in ZONE_IDS
    }
    grab_counts = _allocate_integer_grabs(target_tonnes, grab_size)
    actual_tonnes = {zone_id: round(grab_counts[zone_id] * grab_size, 2) for zone_id in ZONE_IDS}
    sequence = _interleaved_sequence(grab_counts)
    actual_total = sum(actual_tonnes.values()) or 1.0
    actual_percentages = {zone_id: round((actual_tonnes[zone_id] / actual_total) * 100, 1) for zone_id in ZONE_IDS}

    return {
        "planning_note": (
            "Percentages are translated into operator guidance. WasteIQ does not control the crane; "
            "the operator uses weighbridge/crane scale readings or estimated grab counts."
        ),
        "grab_size_tonnes": round(grab_size, 2),
        "target_tonnes_by_zone": target_tonnes,
        "estimated_grabs_by_zone": grab_counts,
        "actual_tonnes_by_estimated_grabs": actual_tonnes,
        "actual_percentages_by_estimated_grabs": actual_percentages,
        "loading_sequence": sequence,
        "operator_instruction": (
            "Load the target tonnes by zone when crane scale data is available. "
            "If working by grabs, follow the interleaved sequence to avoid feeding one zone in a large block."
        ),
    }


def simulate_zone_mix(
    zones: list[dict[str, Any]],
    low_pct: float,
    medium_pct: float,
    high_pct: float,
    feed_rate_tonnes_per_hour: float = 10,
    duration_hours: float = 2,
) -> dict[str, Any]:
    percentages = _mix_from_payload(low_pct, medium_pct, high_pct)
    total_pct = sum(percentages.values())
    total_feed_mass = max(float(feed_rate_tonnes_per_hour), 0.0) * max(float(duration_hours), 0.0)
    zones_by_id = _zone_map(zones)
    warnings: list[str] = []

    if abs(total_pct - 100) > 0.001:
        warnings.append("Mix percentages must sum to 100%.")

    blended_cv = 0.0
    consumed_by_zone: dict[str, float] = {}
    remaining_by_zone: dict[str, float] = {}
    exhaustion_risk_by_zone: dict[str, float] = {}

    for zone_id in ZONE_IDS:
        zone = zones_by_id.get(zone_id, {})
        pct = percentages.get(zone_id, 0.0)
        share = pct / 100
        avg_cv = float(zone.get("avg_cv", 0.0) or 0.0)
        available = float(zone.get("available_mass_tonnes", 0.0) or 0.0)
        consumed = total_feed_mass * share
        blended_cv += share * avg_cv

        if pct > 0 and available <= 0:
            warnings.append(f"{zone_id} zone has no available mass.")
        if consumed > available + 0.001:
            warnings.append(f"{zone_id} zone does not have enough mass for this 2-hour feed plan.")

        consumed_by_zone[zone_id] = round(consumed, 2)
        remaining_by_zone[zone_id] = round(max(available - consumed, 0.0), 2)
        exhaustion_risk_by_zone[zone_id] = round((consumed / available) if available > 0 else (1.0 if consumed > 0 else 0.0), 3)

    is_cv_safe = settings.safe_cv_min <= blended_cv <= settings.safe_cv_max
    if not is_cv_safe:
        warnings.append("Blended CV is outside the safe operating band.")

    return {
        "input_mix_percentages": percentages,
        "blended_cv": round_cv(blended_cv),
        "is_cv_safe": is_cv_safe,
        "target_error": round(_target_error(blended_cv), 2),
        "total_feed_mass_tonnes": round(total_feed_mass, 2),
        "feed_rate_tonnes_per_hour": round(float(feed_rate_tonnes_per_hour), 2),
        "duration_hours": round(float(duration_hours), 2),
        "crane_plan": build_crane_plan(percentages, total_feed_mass),
        "consumed_by_zone": consumed_by_zone,
        "remaining_by_zone": remaining_by_zone,
        "exhaustion_risk_by_zone": exhaustion_risk_by_zone,
        "max_exhaustion_risk": round(max(exhaustion_risk_by_zone.values()) if exhaustion_risk_by_zone else 0.0, 3),
        "is_feasible": len([warning for warning in warnings if "safe operating band" not in warning]) == 0,
        "warnings": warnings,
    }


def _candidate_percentages() -> list[dict[str, float]]:
    candidates: list[dict[str, float]] = []
    for low in range(0, 101, 5):
        for medium in range(0, 101 - low, 5):
            high = 100 - low - medium
            candidates.append({"LOW": float(low), "MEDIUM": float(medium), "HIGH": float(high)})
    return candidates


def score_zone_simulation(simulation: dict[str, Any]) -> tuple[float, dict[str, float]]:
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


def optimize_zone_mix(
    zones: list[dict[str, Any]],
    feed_rate_tonnes_per_hour: float = 10,
    duration_hours: float = 2,
) -> dict[str, Any]:
    best: dict[str, Any] | None = None

    for mix in _candidate_percentages():
        simulation = simulate_zone_mix(
            zones,
            mix["LOW"],
            mix["MEDIUM"],
            mix["HIGH"],
            feed_rate_tonnes_per_hour,
            duration_hours,
        )
        if not simulation["is_feasible"]:
            continue

        score, score_metrics = score_zone_simulation(simulation)
        candidate = {
            "recommended_mix": simulation["input_mix_percentages"],
            "mix_percentages": simulation["input_mix_percentages"],
            "simulation": simulation,
            "expected_cv": simulation["blended_cv"],
            "consumed_by_zone": simulation["consumed_by_zone"],
            "remaining_by_zone": simulation["remaining_by_zone"],
            "exhaustion_risk_by_zone": simulation["exhaustion_risk_by_zone"],
            "score": score,
            "score_metrics": score_metrics,
            "is_safe": simulation["is_cv_safe"],
            "is_feasible": simulation["is_feasible"],
        }
        if best is None or candidate["score"] < best["score"]:
            best = candidate

    if best is None:
        empty = simulate_zone_mix(zones, 0, 100, 0, feed_rate_tonnes_per_hour, duration_hours)
        return {
            "recommended_mix": empty["input_mix_percentages"],
            "mix_percentages": empty["input_mix_percentages"],
            "simulation": empty,
            "expected_cv": empty["blended_cv"],
            "consumed_by_zone": empty["consumed_by_zone"],
            "remaining_by_zone": empty["remaining_by_zone"],
            "exhaustion_risk_by_zone": empty["exhaustion_risk_by_zone"],
            "score": 999.0,
            "score_metrics": {},
            "explanation": "No feasible zone mix is available for the requested feed plan.",
            "why_this_mix_is_best": "No feasible candidate mix was found.",
            "why_not_overuse_one_zone": "WasteIQ will not recommend consuming more mass than a virtual zone contains.",
            "is_safe": empty["is_cv_safe"],
            "is_feasible": False,
        }

    mix = best["mix_percentages"]
    primary_zone = max(mix, key=mix.get)
    best["explanation"] = (
        f"WasteIQ selected {mix['LOW']:.0f}% Low, {mix['MEDIUM']:.0f}% Medium, and {mix['HIGH']:.0f}% High CV material "
        f"to keep the blended feed near {settings.target_cv:.0f} MJ/kg while limiting zone depletion."
    )
    best["why_this_mix_is_best"] = (
        f"It scored lowest because the expected CV is {best['simulation']['blended_cv']} MJ/kg, "
        f"target error is {best['simulation']['target_error']}, and max zone exhaustion is "
        f"{round(best['simulation']['max_exhaustion_risk'] * 100)}%."
    )
    best["why_not_overuse_one_zone"] = (
        f"The largest share is {mix[primary_zone]:.0f}% from {primary_zone}; the scoring penalizes one-zone dominance "
        "and scarce-zone depletion, so high-value reserve is not consumed unless needed for CV control."
    )
    return best


def default_naive_mix(zones: list[dict[str, Any]]) -> dict[str, Any]:
    simulation = simulate_zone_mix(
        zones,
        33,
        34,
        33,
        settings.default_feed_rate_tonnes_per_hour,
        settings.default_duration_hours,
    )
    score, score_metrics = score_zone_simulation(simulation)
    return {
        "recommended_mix": simulation["input_mix_percentages"],
        "mix_percentages": simulation["input_mix_percentages"],
        "simulation": simulation,
        "expected_cv": simulation["blended_cv"],
        "consumed_by_zone": simulation["consumed_by_zone"],
        "remaining_by_zone": simulation["remaining_by_zone"],
        "exhaustion_risk_by_zone": simulation["exhaustion_risk_by_zone"],
        "score": score,
        "score_metrics": score_metrics,
        "is_safe": simulation["is_cv_safe"],
        "is_feasible": simulation["is_feasible"],
    }


def build_zone_forecast(current_cv: float, simulation: dict[str, Any]) -> list[dict[str, Any]]:
    expected_cv = float(simulation.get("blended_cv", current_cv))
    points = [("Now", 0), ("+30m", 0.5), ("+1h", 1), ("+90m", 1.5), ("+2h", 2)]
    return [
        {
            "label": label,
            "hour": hour,
            "cv": round_cv(current_cv + ((expected_cv - current_cv) * (hour / 2))),
        }
        for label, hour in points
    ]
