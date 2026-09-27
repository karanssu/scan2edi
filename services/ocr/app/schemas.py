from decimal import Decimal

from pydantic import BaseModel, Field


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


class ExtractedInvoice(BaseModel):
    vendor_name: str | None = None
    invoice_number: str | None = None
    subtotal: Decimal | None = None
    invoice_level_discount: Decimal | None = None
    invoice_total: Decimal | None = None
    lines: list[ExtractedLine] = Field(default_factory=list)
