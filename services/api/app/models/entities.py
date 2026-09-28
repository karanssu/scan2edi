from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def new_id() -> str:
    return str(uuid4())


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    mappings: Mapped[list[VendorProductMapping]] = relationship(back_populates="vendor")
    invoices: Mapped[list[Invoice]] = relationship(back_populates="vendor")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    upc: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    canonical_name: Mapped[str] = mapped_column(String(250))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    mappings: Mapped[list[VendorProductMapping]] = relationship(back_populates="product")


class VendorProductMapping(Base):
    __tablename__ = "vendor_product_mappings"
    __table_args__ = (
        UniqueConstraint("vendor_id", "normalized_description", "units_per_case", name="uq_vendor_description_pack"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    vendor_sku: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    vendor_description: Mapped[str] = mapped_column(String(500))
    normalized_description: Mapped[str] = mapped_column(String(500), index=True)
    units_per_case: Mapped[int] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vendor: Mapped[Vendor] = relationship(back_populates="mappings")
    product: Mapped[Product] = relationship(back_populates="mappings")
    history: Mapped[list[MappingHistory]] = relationship(back_populates="mapping", cascade="all, delete-orphan")


class MappingHistory(Base):
    __tablename__ = "mapping_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    mapping_id: Mapped[str] = mapped_column(ForeignKey("vendor_product_mappings.id"), index=True)
    action: Mapped[str] = mapped_column(String(20), index=True)
    old_upc: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_upc: Mapped[str | None] = mapped_column(String(32), nullable=True)
    old_units_per_case: Mapped[int | None] = mapped_column(Integer, nullable=True)
    new_units_per_case: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_by: Mapped[str] = mapped_column(String(120), default="local-user")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    mapping: Mapped[VendorProductMapping] = relationship(back_populates="history")


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    vendor_id: Mapped[str] = mapped_column(ForeignKey("vendors.id"), index=True)
    invoice_number: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    source_filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="review")
    subtotal: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    invoice_level_discount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    invoice_total: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    vendor: Mapped[Vendor] = relationship(back_populates="invoices")
    lines: Mapped[list[InvoiceLine]] = relationship(back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id"), index=True)
    line_number: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    vendor_sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id"), nullable=True, index=True)

    case_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    units_per_case: Mapped[int | None] = mapped_column(Integer, nullable=True)
    explicit_unit_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    total_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)

    case_price: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    gross_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    product_discount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    explicit_net_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    export_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)

    needs_review: Mapped[bool] = mapped_column(Boolean, default=True)
    review_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    invoice: Mapped[Invoice] = relationship(back_populates="lines")
    product: Mapped[Product | None] = relationship()
