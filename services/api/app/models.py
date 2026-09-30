from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid.uuid4())


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    filename: Mapped[str] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(100))
    source_path: Mapped[str] = mapped_column(Text)
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    invoice_date: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="processing")
    reported_cases: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    reported_units: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    invoice_subtotal: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    invoice_discount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    invoice_deposit: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    invoice_tax: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    invoice_total: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    raw_extraction: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    validation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    lines: Mapped[list["InvoiceLine"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan", order_by="InvoiceLine.sequence"
    )


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    vendor_sku: Mapped[str | None] = mapped_column(String(120), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    printed_upc: Mapped[str | None] = mapped_column(String(32), nullable=True)
    upc: Mapped[str | None] = mapped_column(String(32), nullable=True)
    case_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    units_per_case: Mapped[int | None] = mapped_column(Integer, nullable=True)
    direct_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    total_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    base_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    deposit: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    discount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    sugar_tax: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    line_total: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    export_total: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    needs_review: Mapped[bool] = mapped_column(Boolean, default=True)
    review_reasons: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    invoice: Mapped[Invoice] = relationship(back_populates="lines")


class VendorProductMapping(Base):
    __tablename__ = "vendor_product_mappings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    vendor_name: Mapped[str] = mapped_column(String(255), index=True)
    vendor_sku: Mapped[str | None] = mapped_column(String(120), nullable=True)
    normalized_description: Mapped[str] = mapped_column(String(500), index=True)
    upc: Mapped[str] = mapped_column(String(32))
    units_per_case: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class MappingHistory(Base):
    __tablename__ = "mapping_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    mapping_id: Mapped[str] = mapped_column(String(36), index=True)
    action: Mapped[str] = mapped_column(String(20))
    snapshot: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
