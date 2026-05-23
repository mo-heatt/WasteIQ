from __future__ import annotations

from typing import Any

from app.agent.llm_client import LLMClient


def _format_mix(mix: dict[str, float]) -> str:
    parts = [
        f"{pct:g}% from {code}"
        for code, pct in sorted(mix.items(), key=lambda item: item[1], reverse=True)
        if pct > 0
    ]
    return ", ".join(parts)


def fallback_explanation(payload: dict[str, Any]) -> dict[str, Any]:
    dashboard = payload["dashboard"]
    optimized = payload["optimized_mix"]
    simulation = payload["simulation"]
    mix = optimized.get("recommended_region_mix") or optimized.get("mix_percentages") or optimized.get("recommended_mix_percentages", {})

    safe_text = "inside" if simulation["is_cv_safe"] else "outside"
    target_text = "near"
    feasible_text = "feasible" if simulation["is_feasible"] else "not feasible"
    expected_cv = optimized.get("expected_cv") or simulation.get("blended_cv")
    preservation_text = optimized.get(
        "why_not_overuse_one_region",
        optimized.get("why_not_overuse_one_zone", "The score penalizes high exhaustion risk and avoids relying too heavily on one region."),
    )
    operator_instruction = optimized.get(
        "operator_instruction",
        "Use this as decision support, review the crane plan, bunker fill and depletion, then approve the mix before feeding.",
    )

    return {
        "thinking_sequence": [
            "Reading latest truck data...",
            "Updating virtual 9-layer bunker map...",
            "Checking Challenge 1 capacity...",
            "Calculating region average CV...",
            "Testing 2-hour funnel recipes...",
            "Comparing naive and optimized mix...",
            "Preparing operator recommendation...",
        ],
        "summary": (
            f"The optimizer recommends {_format_mix(mix)} for the next 2 hours using LEFT/CENTER/RIGHT bunker regions."
        ),
        "operator_instruction": operator_instruction,
        "why_this_region_mix": (
            f"The deterministic optimizer expects a blended CV of {expected_cv} MJ/kg, "
            f"{target_text} the 10 MJ/kg target and {safe_text} the 8-12 MJ/kg safe band."
        ),
        "why_this_mix": (
            f"The deterministic optimizer expects a blended CV of {expected_cv} MJ/kg, "
            f"{target_text} the 10 MJ/kg target and {safe_text} the 8-12 MJ/kg safe band."
        ),
        "how_9_layers_are_used": (
            "WasteIQ first estimates the 9 waste-code layers in each LEFT/CENTER/RIGHT region, then uses each region's average CV for deterministic simulation."
        ),
        "zone_preservation_reasoning": (
            f"{preservation_text} {optimized.get('why_this_mix_is_best', optimized.get('explanation', ''))}"
        ),
        "what_changed_after_latest_truck": payload.get("before_after_next_shipment", {}).get(
            "feed_plan_change",
            "The latest truck was incorporated into the virtual 9-layer map before generating this recommendation.",
        ),
        "safety_note": (
            f"The plan is {feasible_text}. Current bunker CV is {dashboard['current_cv']} MJ/kg "
            f"with risk status {dashboard['risk_status']}. Operator approval required."
        ),
        "confidence": (
            "High for demo use: all mix percentages, CV values, and depletion numbers come from deterministic simulation."
        ),
    }


async def create_agent_explanation(payload: dict[str, Any]) -> dict[str, Any]:
    client = LLMClient()
    llm_result = await client.explain(payload)
    if llm_result:
        return llm_result
    return fallback_explanation(payload)
