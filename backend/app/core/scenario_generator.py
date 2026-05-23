from __future__ import annotations

from typing import Any


def demo_story_steps() -> list[dict[str, Any]]:
    """Kept small: frontend demo steps are served by routes_demo."""
    return [
        {"title": "Bunker images estimate availability", "visual_type": "challenge1"},
        {"title": "Shipment records provide waste type and weight", "visual_type": "shipment_table"},
        {"title": "Waste codes become CV values", "visual_type": "waste_mapping"},
        {"title": "Software-defined CV zones are created", "visual_type": "zone_cards"},
        {"title": "Simulator tests possible crane feeding mixes", "visual_type": "simulation"},
        {"title": "Optimizer selects best balanced mix", "visual_type": "optimizer"},
        {"title": "AI explains the recommendation", "visual_type": "agent"},
        {"title": "Operator approves action", "visual_type": "approval"},
    ]
