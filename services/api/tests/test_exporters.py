from decimal import Decimal

from app.services.exporters import _format_quantity


def test_quantity_format():
    assert _format_quantity(Decimal("24.000")) == "24"
    assert _format_quantity(Decimal("1.5")) == "1.5"
