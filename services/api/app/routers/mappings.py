from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import MappingHistory, VendorProductMapping
from app.schemas import MappingCreate, MappingOut, MappingUpdate
from app.services.mapping_service import add_history, normalize_description
from app.services.vendor_rules import canonical_vendor_name

router = APIRouter(prefix="/mappings", tags=["mappings"])


def _get_mapping(db: Session, mapping_id: str) -> VendorProductMapping:
    mapping = db.get(VendorProductMapping, mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping not found")
    return mapping


@router.get("", response_model=list[MappingOut])
def list_mappings(include_inactive: bool = False, db: Session = Depends(get_db)):
    stmt = select(VendorProductMapping).order_by(
        VendorProductMapping.vendor_name,
        VendorProductMapping.normalized_description,
    )
    if not include_inactive:
        stmt = stmt.where(VendorProductMapping.active.is_(True))
    return list(db.scalars(stmt).all())


@router.post("", response_model=MappingOut)
def create_mapping(payload: MappingCreate, db: Session = Depends(get_db)):
    vendor_name = canonical_vendor_name(payload.vendor_name) or payload.vendor_name.strip()
    normalized = normalize_description(payload.description)
    existing = None
    if payload.vendor_sku:
        existing = db.scalar(select(VendorProductMapping).where(
            VendorProductMapping.vendor_name == vendor_name,
            VendorProductMapping.vendor_sku == payload.vendor_sku,
        ))
    if existing is None:
        existing = db.scalar(select(VendorProductMapping).where(
            VendorProductMapping.vendor_name == vendor_name,
            VendorProductMapping.normalized_description == normalized,
        ))
    if existing:
        was_active = existing.active
        existing.vendor_sku = payload.vendor_sku
        existing.upc = payload.upc
        existing.units_per_case = payload.units_per_case
        existing.active = True
        add_history(db, existing, "UPDATE" if was_active else "REACTIVATE")
        db.commit()
        db.refresh(existing)
        return existing

    mapping = VendorProductMapping(
        vendor_name=vendor_name,
        vendor_sku=payload.vendor_sku,
        normalized_description=normalized,
        upc=payload.upc,
        units_per_case=payload.units_per_case,
        active=True,
    )
    db.add(mapping)
    db.flush()
    add_history(db, mapping, "CREATE")
    db.commit()
    db.refresh(mapping)
    return mapping


@router.patch("/{mapping_id}", response_model=MappingOut)
def update_mapping(mapping_id: str, payload: MappingUpdate, db: Session = Depends(get_db)):
    mapping = _get_mapping(db, mapping_id)
    changes = payload.model_dump(exclude_unset=True)
    if "description" in changes:
        mapping.normalized_description = normalize_description(changes.pop("description"))
    for key, value in changes.items():
        setattr(mapping, key, value)
    add_history(db, mapping, "UPDATE")
    db.commit()
    db.refresh(mapping)
    return mapping


@router.delete("/{mapping_id}", response_model=MappingOut)
def delete_mapping(mapping_id: str, db: Session = Depends(get_db)):
    mapping = _get_mapping(db, mapping_id)
    mapping.active = False
    add_history(db, mapping, "DELETE")
    db.commit()
    db.refresh(mapping)
    return mapping


@router.get("/{mapping_id}/history")
def mapping_history(mapping_id: str, db: Session = Depends(get_db)):
    _get_mapping(db, mapping_id)
    stmt = (
        select(MappingHistory)
        .where(MappingHistory.mapping_id == mapping_id)
        .order_by(MappingHistory.created_at.desc())
    )
    return [
        {
            "id": item.id,
            "action": item.action,
            "snapshot": item.snapshot,
            "created_at": item.created_at,
        }
        for item in db.scalars(stmt).all()
    ]
