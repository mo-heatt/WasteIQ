from __future__ import annotations

from collections import Counter
from typing import Any

from fastapi import APIRouter, HTTPException

from app.core.bunker_zones import build_waste_distribution
from app.core.zone_builder import add_virtual_zone_to_shipments
from app.data.clean_shipments import clean_shipments_with_meta
from app.data.load_shipments import ShipmentDataError, load_raw_shipments_with_meta

router = APIRouter(prefix="/api", tags=["dataset"])


def _value(record: dict[str, Any], flat_key: str) -> Any:
    if flat_key in record:
        return record.get(flat_key)
    current: Any = record
    for part in flat_key.split("__"):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


@router.get("/dataset/summary")
def dataset_summary() -> dict[str, Any]:
    try:
        raw_shipments, source_meta = load_raw_shipments_with_meta()
        shipments, _clean_meta = clean_shipments_with_meta()
    except ShipmentDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    missing_weight_count = sum(1 for row in raw_shipments if _value(row, "shipment__weight") in (None, ""))
    missing_waste_code_count = sum(1 for row in raw_shipments if _value(row, "waste_code__code") in (None, ""))
    waste_distribution = build_waste_distribution(shipments)
    latest_shipments = sorted(add_virtual_zone_to_shipments(shipments), key=lambda item: item["timestamp"], reverse=True)[:10]

    return {
        "demo_mode": bool(source_meta.get("demo_mode", False)),
        "data_source_message": source_meta.get("message", ""),
        "total_shipments": len(shipments),
        "total_weight_tonnes": round(sum(float(row["weight_tonnes"]) for row in shipments), 2),
        "unique_waste_codes": sorted(Counter(row["waste_code"] for row in shipments).keys()),
        "first_timestamp": shipments[0]["timestamp"] if shipments else None,
        "latest_timestamp": shipments[-1]["timestamp"] if shipments else None,
        "missing_weight_count": missing_weight_count,
        "missing_waste_code_count": missing_waste_code_count,
        "waste_code_distribution": waste_distribution,
        "latest_shipments": latest_shipments,
    }
