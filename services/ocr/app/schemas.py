from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


def _blank_to_none(value):
    if isinstance(value, str) and not value.strip():
        return None
    return value


class ExtractedLine(BaseModel):
    description: str
    vendor_sku: str | None = None
    case_quantity: Decimal | None = None
    units_per_case: int | None = None
    explicit_unit_quantity: Decimal | None = None
    case_price: Decimal | None = None
    gross_amount: Decimal | None = None
    product_discount: Decimal | None = None
    explicit_net_amount: Decimal | None = None

    @field_validator(
        "case_quantity",
        "units_per_case",
        "explicit_unit_quantity",
        "case_price",
        "gross_amount",
        "product_discount",
        "explicit_net_amount",
        mode="before",
    )
    @classmethod
    def blank_numeric_values_are_missing(cls, value):
        return _blank_to_none(value)


class ExtractedInvoice(BaseModel):
    vendor_name: str | None = None
    invoice_number: str | None = None
    subtotal: Decimal | None = None
    invoice_level_discount: Decimal | None = None
    invoice_total: Decimal | None = None
    lines: list[ExtractedLine] = Field(default_factory=list)

    @field_validator(
        "subtotal",
        "invoice_level_discount",
        "invoice_total",
        mode="before",
    )
    @classmethod
    def blank_numeric_values_are_missing(cls, value):
        return _blank_to_none(value)
