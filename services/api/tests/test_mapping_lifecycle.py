from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.session import Base
from app.models.entities import MappingHistory, Product, Vendor
from app.schemas.domain import InvoiceCreate, InvoiceLineInput
from app.services.invoices import build_invoice
from app.services.mapping import create_or_replace_mapping, deactivate_mapping, update_mapping


def make_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_mapping_can_be_updated_without_rewriting_existing_invoice_line():
    with make_session() as db:
        vendor = Vendor(name="Coca-Cola")
        db.add(vendor)
        db.flush()

        mapping = create_or_replace_mapping(
            db,
            vendor_id=vendor.id,
            vendor_sku="COKE20",
            vendor_description="Coke 20oz 24pk",
            units_per_case=24,
            upc="111111111111",
            canonical_name="Coke 20oz",
        )
        original_product_id = mapping.product_id

        invoice = build_invoice(
            db,
            InvoiceCreate(
                vendor_id=vendor.id,
                invoice_number="INV-1",
                lines=[
                    InvoiceLineInput(
                        description="Coke 20oz 24pk",
                        vendor_sku="COKE20",
                        case_quantity=Decimal("2"),
                        units_per_case=24,
                        gross_amount=Decimal("60.00"),
                        product_discount=Decimal("5.00"),
                    )
                ],
            ),
        )
        historical_line = invoice.lines[0]
        assert historical_line.product_id == original_product_id
        assert historical_line.total_quantity == Decimal("48")
        assert historical_line.export_amount == Decimal("55.00")

        update_mapping(
            db,
            mapping=mapping,
            upc="222222222222",
            canonical_name="Coke 20oz New UPC",
            units_per_case=24,
            reason="UPC changed",
        )
        db.flush()

        assert mapping.product_id != original_product_id
        assert historical_line.product_id == original_product_id
        assert db.get(Product, historical_line.product_id).upc == "111111111111"
        assert db.get(Product, mapping.product_id).upc == "222222222222"

        actions = list(
            db.scalars(
                select(MappingHistory.action)
                .where(MappingHistory.mapping_id == mapping.id)
                .order_by(MappingHistory.created_at)
            )
        )
        assert actions == ["CREATE", "UPDATE"]


def test_deleted_mapping_becomes_inactive_and_keeps_audit_history():
    with make_session() as db:
        vendor = Vendor(name="Coca-Cola")
        db.add(vendor)
        db.flush()

        mapping = create_or_replace_mapping(
            db,
            vendor_id=vendor.id,
            vendor_sku=None,
            vendor_description="Sprite 20oz 24pk",
            units_per_case=24,
            upc="333333333333",
            canonical_name="Sprite 20oz",
        )
        deactivate_mapping(db, mapping=mapping, reason="Wrong barcode")
        db.flush()

        assert mapping.active is False
        history = list(
            db.scalars(
                select(MappingHistory)
                .where(MappingHistory.mapping_id == mapping.id)
                .order_by(MappingHistory.created_at)
            )
        )
        assert [entry.action for entry in history] == ["CREATE", "DELETE"]
        assert history[-1].old_upc == "333333333333"
        assert history[-1].new_upc is None
        assert history[-1].reason == "Wrong barcode"


def test_deleted_mapping_can_be_reactivated_instead_of_duplicated():
    with make_session() as db:
        vendor = Vendor(name="Coca-Cola")
        db.add(vendor)
        db.flush()

        mapping = create_or_replace_mapping(
            db,
            vendor_id=vendor.id,
            vendor_sku=None,
            vendor_description="Dasani 20oz 24pk",
            units_per_case=24,
            upc="444444444444",
            canonical_name="Dasani 20oz",
        )
        original_mapping_id = mapping.id
        deactivate_mapping(db, mapping=mapping)
        db.flush()

        remapped = create_or_replace_mapping(
            db,
            vendor_id=vendor.id,
            vendor_sku=None,
            vendor_description="Dasani 20oz 24pk",
            units_per_case=24,
            upc="555555555555",
            canonical_name="Dasani 20oz",
        )
        db.flush()

        assert remapped.id == original_mapping_id
        assert remapped.active is True
        assert db.get(Product, remapped.product_id).upc == "555555555555"
