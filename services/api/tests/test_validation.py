from decimal import Decimal
from types import SimpleNamespace

from app.services.validation import validate_invoice


def line(seq, cases, units, amount, upc="123456789012", review=False):
    return SimpleNamespace(
        sequence=seq,
        case_quantity=cases,
        total_quantity=units,
        export_total=amount,
        upc=upc,
        needs_review=review,
    )


def test_redbull_summary_totals_validate_without_reapplying_discount():
    rows = [
        line(1, Decimal("1"), Decimal("24"), Decimal("39.69")),
        line(2, Decimal("2"), Decimal("24"), Decimal("79.38")),
    ]
    result = validate_invoice(
        rows,
        vendor="Red Bull Distribution Company",
        reported_cases=Decimal("3"),
        reported_units=Decimal("48"),
        invoice_total=Decimal("119.07"),
        invoice_discount=Decimal("22.50"),
    )
    assert result["ready"] is True


def test_bjs_general_receipt_discount_only_affects_validation_not_line_exports():
    rows = [line(1, Decimal("0"), Decimal("1"), Decimal("39.68"))]
    result = validate_invoice(
        rows,
        vendor="BJ's Wholesale Club",
        invoice_total=Decimal("34.68"),
        invoice_discount=Decimal("5.00"),
    )
    assert result["ready"] is True
    assert result["calculated_amount"] == "39.68"
    assert result["expected_invoice_total"] == "34.68"
