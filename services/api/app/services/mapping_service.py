from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MappingHistory, VendorProductMapping


def normalize_description(value: str) -> str:
    value = value.upper().strip()
    value = re.sub(r"[^A-Z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def snapshot(mapping: VendorProductMapping) -> dict:
    return {
        "id": mapping.id,
        "vendor_name": mapping.vendor_name,
        "vendor_sku": mapping.vendor_sku,
        "normalized_description": mapping.normalized_description,
        "upc": mapping.upc,
        "units_per_case": mapping.units_per_case,
        "active": mapping.active,
    }


def add_history(db: Session, mapping: VendorProductMapping, action: str) -> None:
    db.add(MappingHistory(mapping_id=mapping.id, action=action, snapshot=snapshot(mapping)))


def find_mapping(db: Session, vendor: str, vendor_sku: str | None, description: str) -> VendorProductMapping | None:
    if not vendor:
        return None

    if vendor_sku:
        stmt = select(VendorProductMapping).where(
            VendorProductMapping.active.is_(True),
            VendorProductMapping.vendor_name == vendor,
            VendorProductMapping.vendor_sku == vendor_sku,
        )
        found = db.scalar(stmt)
        if found:
            return found

    normalized = normalize_description(description)
    stmt = select(VendorProductMapping).where(
        VendorProductMapping.active.is_(True),
        VendorProductMapping.vendor_name == vendor,
        VendorProductMapping.normalized_description == normalized,
    )
    return db.scalar(stmt)
