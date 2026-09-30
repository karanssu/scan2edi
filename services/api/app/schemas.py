from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExtractedLine(BaseModel):
    confidence: float | None = None
    vendor_sku: str | None = None
    description: str = ""
    printed_upc: str | None = None
    case_quantity: Decimal | None = None
    units_per_case: int | None = None
    direct_quantity: Decimal | None = None
    price: Decimal | None = None
    base_amount: Decimal | None = None
    deposit: Decimal | None = None
    discount: Decimal | None = None
    sugar_tax: Decimal | None = None
    line_total: Decimal | None = None


class ExtractedInvoice(BaseModel):
    vendor: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None
    reported_cases: Decimal | None = None
    reported_units: Decimal | None = None
    invoice_subtotal: Decimal | None = None
    invoice_discount: Decimal | None = None
    invoice_deposit: Decimal | None = None
    invoice_tax: Decimal | None = None
    invoice_total: Decimal | None = None
    lines: list[ExtractedLine] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class InvoiceLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sequence: int
    confidence: float | None
    vendor_sku: str | None
    description: str
    printed_upc: str | None
    upc: str | None
    case_quantity: Decimal | None
    units_per_case: int | None
    direct_quantity: Decimal | None
    total_quantity: Decimal | None
    price: Decimal | None
    base_amount: Decimal | None
    deposit: Decimal | None
    discount: Decimal | None
    sugar_tax: Decimal | None
    line_total: Decimal | None
    export_total: Decimal | None
    needs_review: bool
    review_reasons: list


class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    vendor: str | None
    invoice_number: str | None
    invoice_date: str | None
    status: str
    reported_cases: Decimal | None
    reported_units: Decimal | None
    invoice_discount: Decimal | None
    invoice_tax: Decimal | None
    invoice_total: Decimal | None
    validation: dict | None
    lines: list[InvoiceLineOut] = Field(default_factory=list)


class InvoiceSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    vendor: str | None
    invoice_number: str | None
    status: str


class InvoiceUpdate(BaseModel):
    vendor: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None
    reported_cases: Decimal | None = None
    reported_units: Decimal | None = None
    invoice_discount: Decimal | None = None
    invoice_tax: Decimal | None = None
    invoice_total: Decimal | None = None


def _clean_confirmed_upc(value: str) -> str:
    cleaned = "".join(ch for ch in value if ch.isdigit())
    if not 8 <= len(cleaned) <= 14:
        raise ValueError("UPC/GTIN must contain 8 to 14 digits")
    return cleaned


class InvoiceLineUpdate(BaseModel):
    upc: str | None = None
    units_per_case: int | None = None
    direct_quantity: Decimal | None = None
    case_quantity: Decimal | None = None
    line_total: Decimal | None = None
    base_amount: Decimal | None = None
    deposit: Decimal | None = None
    discount: Decimal | None = None

    @field_validator("upc")
    @classmethod
    def validate_upc(cls, value: str | None) -> str | None:
        return _clean_confirmed_upc(value) if value else None

    @field_validator("units_per_case")
    @classmethod
    def validate_units(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("units_per_case must be greater than zero")
        return value


class LineMappingConfirm(BaseModel):
    upc: str
    units_per_case: int | None = None

    @field_validator("upc")
    @classmethod
    def validate_upc(cls, value: str) -> str:
        return _clean_confirmed_upc(value)

    @field_validator("units_per_case")
    @classmethod
    def validate_units(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("units_per_case must be greater than zero")
        return value


class MappingCreate(BaseModel):
    vendor_name: str
    vendor_sku: str | None = None
    description: str
    upc: str
    units_per_case: int | None = None

    @field_validator("upc")
    @classmethod
    def validate_upc(cls, value: str) -> str:
        return _clean_confirmed_upc(value)

    @field_validator("units_per_case")
    @classmethod
    def validate_units(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("units_per_case must be greater than zero")
        return value


class MappingUpdate(BaseModel):
    vendor_sku: str | None = None
    description: str | None = None
    upc: str | None = None
    units_per_case: int | None = None
    active: bool | None = None

    @field_validator("upc")
    @classmethod
    def validate_upc(cls, value: str | None) -> str | None:
        return _clean_confirmed_upc(value) if value is not None else None

    @field_validator("units_per_case")
    @classmethod
    def validate_units(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("units_per_case must be greater than zero")
        return value


class MappingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    vendor_name: str
    vendor_sku: str | None
    normalized_description: str
    upc: str
    units_per_case: int | None
    active: bool
