from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class VendorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class VendorOut(VendorCreate):
    id: str
    model_config = ConfigDict(from_attributes=True)


class MappingCreate(BaseModel):
    vendor_id: str
    upc: str = Field(min_length=6, max_length=32)
    canonical_name: str
    vendor_description: str
    vendor_sku: str | None = None
    units_per_case: int = Field(gt=0)


class MappingOut(BaseModel):
    id: str
    vendor_id: str
    product_id: str
    vendor_sku: str | None
    vendor_description: str
    normalized_description: str
    units_per_case: int
    upc: str
    canonical_name: str


class InvoiceLineInput(BaseModel):
    description: str
    vendor_sku: str | None = None
    case_quantity: Decimal | None = Field(default=None, ge=0)
    units_per_case: int | None = Field(default=None, gt=0)
    explicit_unit_quantity: Decimal | None = Field(default=None, ge=0)
    case_price: Decimal | None = Field(default=None, ge=0)
    gross_amount: Decimal | None = Field(default=None, ge=0)
    product_discount: Decimal | None = Field(default=None, ge=0)
    explicit_net_amount: Decimal | None = Field(default=None, ge=0)


class InvoiceCreate(BaseModel):
    vendor_id: str
    invoice_number: str | None = None
    subtotal: Decimal | None = None
    invoice_level_discount: Decimal | None = None
    invoice_total: Decimal | None = None
    lines: list[InvoiceLineInput]


class InvoiceLineOut(BaseModel):
    id: str
    line_number: int
    description: str
    vendor_sku: str | None
    upc: str | None
    case_quantity: Decimal | None
    units_per_case: int | None
    total_quantity: Decimal | None
    gross_amount: Decimal | None
    product_discount: Decimal | None
    export_amount: Decimal | None
    needs_review: bool
    review_reason: str | None


class InvoiceOut(BaseModel):
    id: str
    vendor_id: str
    invoice_number: str | None
    status: str
    subtotal: Decimal | None
    invoice_level_discount: Decimal | None
    invoice_total: Decimal | None
    lines: list[InvoiceLineOut]


class ManualMapRequest(BaseModel):
    upc: str
    canonical_name: str
    units_per_case: int = Field(gt=0)
