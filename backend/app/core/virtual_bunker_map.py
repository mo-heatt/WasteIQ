from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from app.core.cv_calculator import risk_status, round_cv
from app.core.region_mapper import REGION_IDS, REGION_MEANINGS, preferred_region_for_cv, regions_by_id
from app.data.waste_code_mapping import WASTE_CV, UNKNOWN_CODE, cv_for_waste_code, name_for_waste_code


FALLBACK_REGION_CV = {"LEFT": 9.5, "CENTER": 11.0, "RIGHT": 14.5}


def assign_region_to_shipment(row: dict[str, Any]) -> str:
    return preferred_region_for_cv(float(row.get("cv", 10.0) or 10.0))


def _known_layer_codes() -> list[str]:
    return [code for code in WASTE_CV if code != UNKNOWN_CODE]


def build_virtual_bunker_map(shipments: list[dict[str, Any]], challenge1_state: dict[str, Any]) -> dict[str, Any]:
    regions = regions_by_id(challenge1_state)
    raw_by_region: dict[str, list[dict[str, Any]]] = {region_id: [] for region_id in REGION_IDS}
    for row in shipments:
        raw_by_region[assign_region_to_shipment(row)].append(row)

    region_payloads: list[dict[str, Any]] = []
    total_available = sum(float(regions.get(region_id, {}).get("available_mass_tonnes", 0) or 0) for region_id in REGION_IDS)

    for region_id in REGION_IDS:
        challenge_region = regions.get(region_id, {"region_id": region_id, "fill_percent": 0.0, "available_mass_tonnes": 0.0})
        available_mass = float(challenge_region.get("available_mass_tonnes", 0) or 0)
        fill_percent = float(challenge_region.get("fill_percent", 0) or 0)
        rows = raw_by_region[region_id]
        raw_mass = sum(float(row.get("weight_tonnes", 0) or 0) for row in rows)
        scale = (available_mass / raw_mass) if raw_mass > 0 and available_mass > 0 else 0.0

        mass_by_code: dict[str, float] = defaultdict(float)
        for row in rows:
            code = str(row.get("waste_layer_id") or row.get("waste_code") or UNKNOWN_CODE)
            if code not in WASTE_CV:
                code = UNKNOWN_CODE
            mass_by_code[code] += float(row.get("weight_tonnes", 0) or 0) * scale

        if not mass_by_code and available_mass > 0:
            # Keep the model usable even if the dataset has no rows for a region.
            fallback_code = UNKNOWN_CODE
            mass_by_code[fallback_code] = available_mass

        region_energy_mj = sum(mass_tonnes * 1000 * cv_for_waste_code(code) for code, mass_tonnes in mass_by_code.items())
        composition_mass = sum(mass_by_code.values())
        average_cv = (region_energy_mj / (composition_mass * 1000)) if composition_mass > 0 else FALLBACK_REGION_CV[region_id]
        dominant_code = max(mass_by_code, key=mass_by_code.get) if mass_by_code else UNKNOWN_CODE

        if available_mass <= 0:
            status = "NO_AVAILABLE_MASS"
        elif fill_percent >= 85:
            status = "HIGH_FILL"
        elif available_mass < 10:
            status = "LOW_STOCK"
        else:
            status = "AVAILABLE"

        composition = []
        for code in _known_layer_codes() + ([UNKNOWN_CODE] if UNKNOWN_CODE in mass_by_code else []):
            mass = mass_by_code.get(code, 0.0)
            if mass <= 0 and code == UNKNOWN_CODE:
                continue
            composition.append(
                {
                    "waste_code": code,
                    "name": name_for_waste_code(code),
                    "cv": cv_for_waste_code(code),
                    "estimated_mass_tonnes": round(mass, 2),
                    "percentage_of_region": round((mass / composition_mass) * 100, 1) if composition_mass else 0,
                }
            )

        region_payloads.append(
            {
                "region_id": region_id,
                "region_name": f"{region_id} operational region",
                "operational_meaning": REGION_MEANINGS[region_id],
                "fill_percent": round(fill_percent, 1),
                "available_mass_tonnes": round(available_mass, 2),
                "waste_layer_composition": composition,
                "average_cv": round_cv(average_cv),
                "avg_cv": round_cv(average_cv),
                "total_energy_mj": round(region_energy_mj, 1),
                "dominant_waste_code": dominant_code,
                "dominant_waste_name": name_for_waste_code(dominant_code),
                "region_status": status,
                "source_note": (
                    "Estimated virtual layer composition from shipment waste codes, recommended unloading regions, "
                    "and Challenge 1 region availability. This is not a walled or separated storage area."
                ),
            }
        )

    total_energy = sum(float(region["total_energy_mj"]) for region in region_payloads)
    current_cv = (total_energy / (total_available * 1000)) if total_available > 0 else 0.0
    dominant_region = max(region_payloads, key=lambda item: item["available_mass_tonnes"])["region_id"] if region_payloads else "NONE"
    all_layer_masses: Counter[str] = Counter()
    for region in region_payloads:
        for layer in region["waste_layer_composition"]:
            all_layer_masses[layer["waste_code"]] += float(layer["estimated_mass_tonnes"])
    dominant_layer = all_layer_masses.most_common(1)[0][0] if all_layer_masses else UNKNOWN_CODE

    return {
        "map_type": "software_defined_9_layer_energy_map",
        "source_note": (
            "The bunker is one open pit. WasteIQ maintains an estimated virtual map from shipment records, "
            "recommended unloading region and Challenge 1 bunker availability."
        ),
        "regions": region_payloads,
        "current_cv": round_cv(current_cv),
        "risk_status": risk_status(current_cv),
        "total_available_mass_tonnes": round(total_available, 2),
        "total_energy_mj": round(total_energy, 1),
        "dominant_region": dominant_region,
        "dominant_waste_layer": dominant_layer,
    }
