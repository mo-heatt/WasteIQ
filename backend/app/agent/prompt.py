from __future__ import annotations

import json
from typing import Any


def build_agent_prompt(payload: dict[str, Any]) -> list[dict[str, str]]:
    system = (
        "You are WasteIQ, an operator-facing AI co-pilot for waste-to-energy plants. "
        "You must not calculate, optimize, or invent numerical values. Deterministic code has already "
        "combined Challenge 1 bunker availability, shipment CV history, virtual CV zones, two-hour simulation, optimized mix, crane guidance, and forecast. Explain only those "
        "outputs in clear control-room language. Keep the operator in control."
    )

    user = (
        "Create a concise JSON object with keys summary, operator_instruction, why_this_mix, "
        "zone_preservation_reasoning, safety_note, and confidence. Use the deterministic data below "
        "and do not add new calculations.\n\n"
        f"{json.dumps(payload, indent=2)}"
    )

    return [{"role": "system", "content": system}, {"role": "user", "content": user}]
