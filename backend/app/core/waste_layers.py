from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.core.region_mapper import preferred_region_for_cv
from app.data.waste_code_mapping import UNKNOWN_CODE, WASTE_CV, cv_for_waste_code, name_for_waste_code


def build_waste_layers(virtual_map: dict[str, Any]) -> list[dict[str, Any]]:
    mass_by_code: dict[str, float] = defaultdict(float)
    for region in virtual_map.get("regions", []):
        for layer in region.get("waste_layer_composition", []):
            mass_by_code[str(layer["waste_code"])] += float(layer.get("estimated_mass_tonnes", 0) or 0)

    total_mass = sum(mass_by_code.values()) or float(virtual_map.get("total_available_mass_tonnes", 0) or 0) or 1.0
    layers: list[dict[str, Any]] = []
    for code, meta in WASTE_CV.items():
        if code == UNKNOWN_CODE and mass_by_code.get(code, 0.0) <= 0:
            continue
        cv = float(meta["cv"])
        mass = mass_by_code.get(code, 0.0)
        layers.append(
            {
                "waste_code": code,
                "name": name_for_waste_code(code),
                "cv": cv,
                "total_estimated_mass_tonnes": round(mass, 2),
                "percentage_of_bunker": round((mass / total_mass) * 100, 1) if total_mass else 0,
                "preferred_region": preferred_region_for_cv(cv),
                "is_unknown_layer": code == UNKNOWN_CODE,
            }
        )
    return layers
