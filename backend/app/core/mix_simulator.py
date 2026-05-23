from __future__ import annotations

from typing import Any

from app.config import settings
from app.core.cv_calculator import round_cv


def _normalise_percentages(raw_percentages: dict[str, float]) -> dict[str, float]:
    return {str(code): float(value) for code, value in raw_percentages.items() if float(value) > 0}


def _target_band_error(cv: float) -> float:
    if settings.target_cv_min <= cv <= settings.target_cv_max:
        return 0.0
    if cv < settings.target_cv_min:
        return settings.target_cv_min - cv
    return cv - settings.target_cv_max


def simulate_bunker_mix(
    bunker_cells: list[dict[str, Any]],
    mix_percentages: dict[str, float],
    feed_rate_tonnes_per_hour: float = 10,
    duration_hours: float = 2,
) -> dict[str, Any]:
    percentages = _normalise_percentages(mix_percentages)
    total_pct = sum(percentages.values())
    total_feed_mass = max(float(feed_rate_tonnes_per_hour), 0) * max(float(duration_hours), 0)
    cells = {cell["waste_code"]: cell for cell in bunker_cells}
    infeasible_reasons: list[str] = []

    if abs(total_pct - 100) > 0.001:
        infeasible_reasons.append("Mix percentages must sum to 100%.")

    blended_cv = 0.0
    consumed_by_bunker: dict[str, float] = {}
    remaining_by_bunker: dict[str, float] = {}
    projected_mass_after_2h: dict[str, float] = {}
    projected_fill_after_2h: dict[str, float] = {}
    exhaustion_risk_by_bunker: dict[str, float] = {}
    consumed_by_zone = {"LOW": 0.0, "MEDIUM": 0.0, "HIGH": 0.0}

    for code, cell in cells.items():
        pct = percentages.get(code, 0.0)
        share = pct / 100
        available = float(cell["available_mass_tonnes"])
        consumed = total_feed_mass * share
        capacity = float(cell["capacity_tonnes"])
        incoming = float(cell.get("projected_incoming_2h_tonnes", 0))

        if pct > 0 and available <= 0:
            infeasible_reasons.append(f"{code} bunker has no available mass.")
        if consumed > available + 0.001:
            infeasible_reasons.append(f"{code} bunker does not have enough mass for this feed plan.")

        blended_cv += share * float(cell["cv"])
        remaining = max(available - consumed, 0.0)
        projected_mass = max(available - consumed + incoming, 0.0)
        projected_fill = (projected_mass / capacity) * 100 if capacity else 0.0

        consumed_by_bunker[code] = round(consumed, 2)
        remaining_by_bunker[code] = round(remaining, 2)
        projected_mass_after_2h[code] = round(projected_mass, 2)
        projected_fill_after_2h[code] = round(projected_fill, 1)
        exhaustion_risk_by_bunker[code] = round((consumed / available) if available > 0 else (1.0 if consumed > 0 else 0.0), 3)
        consumed_by_zone[cell["cv_class"]] += consumed

        if projected_fill > 100:
            infeasible_reasons.append(f"{code} bunker is projected to exceed storage capacity after incoming trucks.")

    is_cv_safe = settings.safe_cv_min <= blended_cv <= settings.safe_cv_max
    is_target_band = settings.target_cv_min <= blended_cv <= settings.target_cv_max

    return {
        "input_mix_percentages": {code: round(value, 1) for code, value in percentages.items()},
        "blended_cv": round_cv(blended_cv),
        "total_feed_mass_tonnes": round(total_feed_mass, 2),
        "feed_rate_tonnes_per_hour": round(float(feed_rate_tonnes_per_hour), 2),
        "duration_hours": round(float(duration_hours), 2),
        "consumed_by_bunker": consumed_by_bunker,
        "remaining_by_bunker": remaining_by_bunker,
        "projected_mass_after_2h": projected_mass_after_2h,
        "projected_fill_after_2h": projected_fill_after_2h,
        "exhaustion_risk_by_bunker": exhaustion_risk_by_bunker,
        "consumed_by_zone": {zone: round(value, 2) for zone, value in consumed_by_zone.items()},
        "is_feasible": len(infeasible_reasons) == 0,
        "infeasible_reasons": infeasible_reasons,
        "is_cv_safe": is_cv_safe,
        "is_target_band": is_target_band,
        "target_error": round(abs(blended_cv - settings.target_cv), 2),
        "target_band_error": round(_target_band_error(blended_cv), 2),
    }


def simulate_mix(
    bunker_cells: list[dict[str, Any]],
    mix_percentages: dict[str, float],
    feed_rate_tonnes_per_hour: float = 10,
    duration_hours: float = 2,
) -> dict[str, Any]:
    return simulate_bunker_mix(bunker_cells, mix_percentages, feed_rate_tonnes_per_hour, duration_hours)
