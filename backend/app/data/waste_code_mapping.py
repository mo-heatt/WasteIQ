from __future__ import annotations

UNKNOWN_CODE = "UNKNOWN"
UNKNOWN_CV = 10.0

WASTE_CV: dict[str, dict[str, float | str]] = {
    "191212": {
        "name": "Other wastes from mechanical treatment",
        "cv": 11.0,
    },
    "200301": {
        "name": "Mixed municipal solid waste",
        "cv": 9.5,
    },
    "180104": {
        "name": "Non-infectious healthcare waste",
        "cv": 14.0,
    },
    "191210": {
        "name": "Combustible waste / RDF",
        "cv": 15.0,
    },
    "200307": {
        "name": "Bulky waste",
        "cv": 15.0,
    },
    "170904": {
        "name": "Mixed construction and demolition waste",
        "cv": 13.0,
    },
    "150106": {
        "name": "Mixed packaging",
        "cv": 16.0,
    },
    "170604": {
        "name": "Insulation materials",
        "cv": 18.0,
    },
    "190801": {
        "name": "Screenings from wastewater treatment",
        "cv": 15.0,
    },
    UNKNOWN_CODE: {
        "name": "Unknown waste code",
        "cv": UNKNOWN_CV,
    },
}

WASTE_BUNKER_CAPACITY_TONNES: dict[str, float] = {
    "191212": 220.0,
    "200301": 450.0,
    "180104": 80.0,
    "191210": 80.0,
    "200307": 80.0,
    "170904": 100.0,
    "150106": 80.0,
    "170604": 60.0,
    "190801": 80.0,
    UNKNOWN_CODE: 120.0,
}


def normalize_waste_code(raw_code: object) -> str:
    if raw_code is None:
        return UNKNOWN_CODE

    code = str(raw_code).strip()
    return code or UNKNOWN_CODE


def cv_for_waste_code(raw_code: object) -> float:
    code = normalize_waste_code(raw_code)
    return float(WASTE_CV.get(code, WASTE_CV[UNKNOWN_CODE])["cv"])


def name_for_waste_code(raw_code: object, fallback: str | None = None) -> str:
    code = normalize_waste_code(raw_code)
    if fallback and str(fallback).strip():
        return str(fallback).strip()
    return str(WASTE_CV.get(code, WASTE_CV[UNKNOWN_CODE])["name"])


def known_waste_codes() -> dict[str, dict[str, float | str]]:
    return {code: value for code, value in WASTE_CV.items() if code != UNKNOWN_CODE}


def capacity_for_waste_code(raw_code: object) -> float:
    code = normalize_waste_code(raw_code)
    return WASTE_BUNKER_CAPACITY_TONNES.get(code, WASTE_BUNKER_CAPACITY_TONNES[UNKNOWN_CODE])
