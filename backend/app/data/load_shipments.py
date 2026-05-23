from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import settings


class ShipmentDataError(RuntimeError):
    """Raised when shipment data exists but cannot be parsed."""


DEMO_RAW_SHIPMENTS: list[dict[str, Any]] = [
    {
        "shipment__entry_timestamp": "2026-05-21T06:10:00+02:00",
        "shipment__weight": 9000,
        "waste_code__code": "200301",
        "waste_code__name": "Mixed municipal solid waste",
        "shipment__license_plate": "DEMO-2101",
        "shipment__gate_number": "G1",
    },
    {
        "shipment__entry_timestamp": "2026-05-21T06:42:00+02:00",
        "shipment__weight": 8000,
        "waste_code__code": "191212",
        "waste_code__name": "Other wastes from mechanical treatment",
        "shipment__license_plate": "DEMO-7340",
        "shipment__gate_number": "G2",
    },
    {
        "shipment__entry_timestamp": "2026-05-21T07:28:00+02:00",
        "shipment__weight": 7000,
        "waste_code__code": "200301",
        "waste_code__name": "Mixed municipal solid waste",
        "shipment__license_plate": "DEMO-8821",
        "shipment__gate_number": "G1",
    },
    {
        "shipment__entry_timestamp": "2026-05-21T08:15:00+02:00",
        "shipment__weight": 5000,
        "waste_code__code": "170904",
        "waste_code__name": "Mixed construction and demolition waste",
        "shipment__license_plate": "DEMO-6204",
        "shipment__gate_number": "G2",
    },
    {
        "shipment__entry_timestamp": "2026-05-21T09:20:00+02:00",
        "shipment__weight": 8000,
        "waste_code__code": "200301",
        "waste_code__name": "Mixed municipal solid waste",
        "shipment__license_plate": "DEMO-4982",
        "shipment__gate_number": "G3",
    },
    {
        "shipment__entry_timestamp": "2026-05-21T10:35:00+02:00",
        "shipment__weight": 5000,
        "waste_code__code": "180104",
        "waste_code__name": "Non-infectious healthcare waste",
        "shipment__license_plate": "DEMO-7825",
        "shipment__gate_number": "G1",
    },
    {
        "shipment__entry_timestamp": "2026-05-21T11:12:00+02:00",
        "shipment__weight": 5000,
        "waste_code__code": "191210",
        "waste_code__name": "Combustible waste / RDF",
        "shipment__license_plate": "DEMO-9408",
        "shipment__gate_number": "G2",
    },
    {
        "shipment__entry_timestamp": "2026-05-21T11:46:00+02:00",
        "shipment__weight": 4000,
        "waste_code__code": "150106",
        "waste_code__name": "Mixed packaging",
        "shipment__license_plate": "DEMO-3002",
        "shipment__gate_number": "G1",
    },
    {
        "shipment__entry_timestamp": "2026-05-21T12:18:00+02:00",
        "shipment__weight": 3000,
        "waste_code__code": "170604",
        "waste_code__name": "Insulation materials",
        "shipment__license_plate": "DEMO-7120",
        "shipment__gate_number": "G3",
    },
]


def load_raw_shipments_with_meta(path: Path | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    configured_path = path or settings.shipments_path
    shipment_path = configured_path
    if not shipment_path.exists() and path is None and settings.public_shipments_path.exists():
        shipment_path = settings.public_shipments_path

    if not shipment_path.exists():
        return DEMO_RAW_SHIPMENTS, {
            "demo_mode": True,
            "source": str(configured_path),
            "message": "Demo data mode: no shipments.json was found in data/ or public-files/, so generated sample shipments are being used.",
        }

    try:
        with shipment_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except json.JSONDecodeError as exc:
        raise ShipmentDataError(f"Shipment file is not valid JSON: {exc}") from exc

    if isinstance(payload, list):
        rows = [item for item in payload if isinstance(item, dict)]
    elif isinstance(payload, dict):
        rows = []
        for key in ("shipments", "data", "results"):
            possible_rows = payload.get(key)
            if isinstance(possible_rows, list):
                rows = [item for item in possible_rows if isinstance(item, dict)]
                break
    else:
        rows = []

    if not rows:
        raise ShipmentDataError("Shipment file must contain a JSON array or an object with a shipments array.")

    return rows, {
        "demo_mode": False,
        "source": str(shipment_path),
        "message": f"Loaded shipment data from {shipment_path}.",
    }


def load_raw_shipments(path: Path | None = None) -> list[dict[str, Any]]:
    rows, _meta = load_raw_shipments_with_meta(path)
    return rows
