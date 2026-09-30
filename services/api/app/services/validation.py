from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from app.models import InvoiceLine
from app.services.vendor_rules import vendor_family

TOLERANCE = Decimal("0.01")
ZERO = Decimal("0")


def _as_decimal(value) -> Decimal | None:
    return Decimal(str(value)) if value is not None else None


def validate_invoice(
    lines: Iterable[InvoiceLine],
    *,
    vendor: str | None = None,
    reported_cases=None,
    reported_units=None,
    invoice_total=None,
    invoice_discount=None,
    invoice_tax=None,
) -> dict:
    lines = list(lines)
    issues: list[str] = []
    warnings: list[str] = []

    calculated_cases = sum((_as_decimal(line.case_quantity) or ZERO) for line in lines)
    calculated_units = sum((_as_decimal(line.total_quantity) or ZERO) for line in lines)
    calculated_amount = sum((_as_decimal(line.export_total) or ZERO) for line in lines)

    if not lines:
        issues.append("No product lines were extracted")

    for line in lines:
        if line.needs_review:
            issues.append(f"Line {line.sequence} requires review")
        if not line.upc:
            issues.append(f"Line {line.sequence} has no confirmed UPC")

    rc = _as_decimal(reported_cases)
    ru = _as_decimal(reported_units)
    it = _as_decimal(invoice_total)
    invoice_discount_value = _as_decimal(invoice_discount) or ZERO
    invoice_tax_value = _as_decimal(invoice_tax) or ZERO

    if rc is not None and calculated_cases != rc:
        issues.append(f"Case total mismatch: calculated {calculated_cases} vs invoice {rc}")
    if ru is not None and calculated_units != ru:
        issues.append(f"Unit total mismatch: calculated {calculated_units} vs invoice {ru}")

    expected_invoice_total: Decimal | None = None
    family = vendor_family(vendor)
    if it is not None:
        if family in {"bjs", "market_basket"}:
            # For these receipt formats, invoice_discount is defined as an invoice-level
            # promotion only. Product-specific coupons are already applied per line.
            expected_invoice_total = calculated_amount - abs(invoice_discount_value) + invoice_tax_value
        elif family in {"redbull", "polar", "paul_henry", "gl_distribution", "coca_cola"}:
            # Their configured line_total is the final product-line amount. Summary
            # deposit/discount fields are informational and must not be applied twice.
            expected_invoice_total = calculated_amount
        elif invoice_discount_value == ZERO and invoice_tax_value == ZERO:
            expected_invoice_total = calculated_amount
        else:
            warnings.append("Invoice amount comparison skipped for an unknown vendor with invoice-level adjustments")

    if it is not None and expected_invoice_total is not None and abs(expected_invoice_total - it) > TOLERANCE:
        issues.append(
            f"Amount total mismatch: expected {expected_invoice_total:.2f} vs invoice {it:.2f}"
        )

    return {
        "ready": not issues,
        "issues": issues,
        "warnings": warnings,
        "calculated_cases": str(calculated_cases),
        "calculated_units": str(calculated_units),
        "calculated_amount": f"{calculated_amount:.2f}",
        "expected_invoice_total": f"{expected_invoice_total:.2f}" if expected_invoice_total is not None else None,
        "reported_cases": str(rc) if rc is not None else None,
        "reported_units": str(ru) if ru is not None else None,
        "invoice_total": f"{it:.2f}" if it is not None else None,
    }
