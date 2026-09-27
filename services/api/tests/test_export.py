from decimal import Decimal
from types import SimpleNamespace

from app.services.export import invoice_to_csv


def test_csv_has_required_three_columns():
    line = SimpleNamespace(
        line_number=1,
        needs_review=False,
        product=SimpleNamespace(upc="049000028904"),
        total_quantity=Decimal("48"),
        export_amount=Decimal("55.00"),
    )
    invoice = SimpleNamespace(lines=[line])
    assert invoice_to_csv(invoice) == (
        "UPC Code,Quantity,Total Amount\n"
        "049000028904,48,55.00\n"
    )
