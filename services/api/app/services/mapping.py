from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import MappingHistory, Product, VendorProductMapping
from app.services.normalization import normalize_description


def find_mapping(
    db: Session,
    *,
    vendor_id: str,
    vendor_sku: str | None,
    description: str,
    units_per_case: int | None,
) -> VendorProductMapping | None:
    if vendor_sku:
        mapping = db.scalar(
            select(VendorProductMapping).where(
                VendorProductMapping.vendor_id == vendor_id,
                VendorProductMapping.vendor_sku == vendor_sku,
                VendorProductMapping.active.is_(True),
            )
        )
        if mapping:
            return mapping

    normalized = normalize_description(description)
    conditions = [
        VendorProductMapping.vendor_id == vendor_id,
        VendorProductMapping.normalized_description == normalized,
        VendorProductMapping.active.is_(True),
    ]
    if units_per_case is not None:
        conditions.append(VendorProductMapping.units_per_case == units_per_case)

    return db.scalar(select(VendorProductMapping).where(*conditions))


def get_or_create_product(db: Session, upc: str, canonical_name: str) -> Product:
    product = db.scalar(select(Product).where(Product.upc == upc))
    if product:
        if canonical_name and product.canonical_name != canonical_name:
            product.canonical_name = canonical_name
        return product
    product = Product(upc=upc, canonical_name=canonical_name)
    db.add(product)
    db.flush()
    return product


def _record_history(
    db: Session,
    *,
    mapping: VendorProductMapping,
    action: str,
    old_upc: str | None,
    new_upc: str | None,
    old_units_per_case: int | None,
    new_units_per_case: int | None,
    reason: str | None = None,
) -> None:
    db.add(
        MappingHistory(
            mapping_id=mapping.id,
            action=action,
            old_upc=old_upc,
            new_upc=new_upc,
            old_units_per_case=old_units_per_case,
            new_units_per_case=new_units_per_case,
            reason=reason,
            changed_by="local-user",
        )
    )


def create_or_replace_mapping(
    db: Session,
    *,
    vendor_id: str,
    vendor_sku: str | None,
    vendor_description: str,
    units_per_case: int,
    upc: str,
    canonical_name: str,
    reason: str | None = None,
) -> VendorProductMapping:
    normalized = normalize_description(vendor_description)

    mapping: VendorProductMapping | None = None
    if vendor_sku:
        mapping = db.scalar(
            select(VendorProductMapping).where(
                VendorProductMapping.vendor_id == vendor_id,
                VendorProductMapping.vendor_sku == vendor_sku,
            )
        )

    if mapping is None:
        mapping = db.scalar(
            select(VendorProductMapping).where(
                VendorProductMapping.vendor_id == vendor_id,
                VendorProductMapping.normalized_description == normalized,
                VendorProductMapping.units_per_case == units_per_case,
            )
        )

    product = get_or_create_product(db, upc, canonical_name)

    if mapping is None:
        mapping = VendorProductMapping(
            vendor_id=vendor_id,
            product_id=product.id,
            vendor_sku=vendor_sku,
            vendor_description=vendor_description,
            normalized_description=normalized,
            units_per_case=units_per_case,
            active=True,
        )
        db.add(mapping)
        db.flush()
        _record_history(
            db,
            mapping=mapping,
            action="CREATE",
            old_upc=None,
            new_upc=upc,
            old_units_per_case=None,
            new_units_per_case=units_per_case,
            reason=reason,
        )
        return mapping

    old_product = db.get(Product, mapping.product_id)
    old_upc = old_product.upc if old_product else None
    old_units = mapping.units_per_case
    was_active = mapping.active

    mapping.product_id = product.id
    mapping.vendor_sku = vendor_sku
    mapping.vendor_description = vendor_description
    mapping.normalized_description = normalized
    mapping.units_per_case = units_per_case
    mapping.active = True
    mapping.updated_at = datetime.utcnow()
    db.flush()

    _record_history(
        db,
        mapping=mapping,
        action="UPDATE",
        old_upc=old_upc,
        new_upc=upc,
        old_units_per_case=old_units,
        new_units_per_case=units_per_case,
        reason=reason or ("Mapping reactivated" if not was_active else None),
    )
    return mapping


def update_mapping(
    db: Session,
    *,
    mapping: VendorProductMapping,
    upc: str,
    canonical_name: str,
    units_per_case: int,
    reason: str | None = None,
) -> VendorProductMapping:
    old_product = db.get(Product, mapping.product_id)
    old_upc = old_product.upc if old_product else None
    old_units = mapping.units_per_case

    product = get_or_create_product(db, upc, canonical_name)
    mapping.product_id = product.id
    mapping.units_per_case = units_per_case
    mapping.active = True
    mapping.updated_at = datetime.utcnow()
    db.flush()

    _record_history(
        db,
        mapping=mapping,
        action="UPDATE",
        old_upc=old_upc,
        new_upc=upc,
        old_units_per_case=old_units,
        new_units_per_case=units_per_case,
        reason=reason,
    )
    return mapping


def deactivate_mapping(
    db: Session,
    *,
    mapping: VendorProductMapping,
    reason: str | None = None,
) -> None:
    product = db.get(Product, mapping.product_id)
    old_upc = product.upc if product else None
    old_units = mapping.units_per_case

    mapping.active = False
    mapping.updated_at = datetime.utcnow()
    db.flush()

    _record_history(
        db,
        mapping=mapping,
        action="DELETE",
        old_upc=old_upc,
        new_upc=None,
        old_units_per_case=old_units,
        new_units_per_case=None,
        reason=reason,
    )
