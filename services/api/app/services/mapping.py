from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.entities import Product, VendorProductMapping
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
        return product
    product = Product(upc=upc, canonical_name=canonical_name)
    db.add(product)
    db.flush()
    return product
