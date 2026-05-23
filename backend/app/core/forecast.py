from __future__ import annotations

from typing import Any

from app.core.cv_calculator import round_cv


def build_two_hour_forecast(current_cv: float, optimized_mix: dict[str, Any]) -> list[dict[str, Any]]:
    expected_cv = float(optimized_mix.get("expected_cv", current_cv))
    max_exhaustion = float(optimized_mix.get("score_metrics", {}).get("max_exhaustion_risk", 0))
    drift_bias = 0.15 if max_exhaustion > 0.65 else 0.0
    points = [
        ("Now", 0),
        ("+30m", 0.5),
        ("+1h", 1),
        ("+90m", 1.5),
        ("+2h", 2),
    ]

    forecast = []
    for label, hour in points:
        progress = hour / 2
        cv = current_cv + ((expected_cv - current_cv) * progress) + (drift_bias * progress)
        forecast.append({"label": label, "hour": hour, "cv": round_cv(cv)})
    return forecast
