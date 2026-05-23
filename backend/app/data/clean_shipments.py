from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from app.data.load_shipments import load_raw_shipments_with_meta
from app.data.waste_code_mapping import cv_for_waste_code, name_for_waste_code, normalize_waste_code


def _value(record: dict[str, Any], flat_key: str) -> Any:
    if flat_key in record:
        return record.get(flat_key)

    current: Any = record
    for part in flat_key.split("__"):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _timestamp_sort_key(timestamp: str) -> datetime:
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min


def _assigned_cv_zone(cv: float) -> str:
    if cv < 9:
        return "LOW"
    if cv <= 12:
        return "MEDIUM"
    return "HIGH"


def clean_shipments_with_meta() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_shipments, meta = load_raw_shipments_with_meta()
    cleaned: list[dict[str, Any]] = []

    for record in raw_shipments:
        timestamp = _value(record, "shipment__entry_timestamp")
        weight_kg = _float_or_none(_value(record, "shipment__weight"))

        if not timestamp or weight_kg is None:
            continue

        waste_code = normalize_waste_code(_value(record, "waste_code__code"))
        raw_name = _value(record, "waste_code__name")
        waste_name = name_for_waste_code(waste_code, raw_name)
        cv = cv_for_waste_code(waste_code)

        cleaned.append(
            {
                "timestamp": str(timestamp),
                "weight_kg": weight_kg,
                "weight_tonnes": weight_kg / 1000,
                "waste_code": waste_code,
                "waste_name": waste_name,
                "truck_id": _value(record, "shipment__license_plate") or "Unknown truck",
                "gate_number": _value(record, "shipment__gate_number") or "Unknown gate",
                "cv": cv,
                "energy_mj": weight_kg * cv,
                "waste_layer_id": waste_code,
                "assigned_cv_zone": _assigned_cv_zone(cv),
            }
        )

    if not cleaned:
        return [], {**meta, "message": f"{meta['message']} No valid rows remained after cleaning."}

    frame = pd.DataFrame(cleaned)
    frame["_sort_timestamp"] = frame["timestamp"].map(_timestamp_sort_key)
    frame = frame.sort_values("_sort_timestamp").drop(columns=["_sort_timestamp"])
    return frame.to_dict(orient="records"), meta


def clean_shipments() -> list[dict[str, Any]]:
    shipments, _meta = clean_shipments_with_meta()
    return shipments
