from decimal import Decimal

from app.services.calculations import calculate_line


def test_case_quantity_becomes_total_units():
    result = calculate_line(
        case_quantity=Decimal("2"),
        units_per_case=24,
        explicit_unit_quantity=None,
        case_price=Decimal("30"),
        gross_amount=Decimal("60"),
        product_discount=None,
        explicit_net_amount=None,
    )
    assert result.total_quantity == Decimal("48")
    assert result.export_amount == Decimal("60.00")


def test_product_discount_reduces_product_total():
    result = calculate_line(
        case_quantity=Decimal("2"),
        units_per_case=24,
        explicit_unit_quantity=None,
        case_price=Decimal("30"),
        gross_amount=Decimal("60"),
        product_discount=Decimal("5"),
        explicit_net_amount=None,
    )
    assert result.total_quantity == Decimal("48")
    assert result.export_amount == Decimal("55.00")


def test_explicit_net_amount_wins():
    result = calculate_line(
        case_quantity=Decimal("2"),
        units_per_case=24,
        explicit_unit_quantity=None,
        case_price=Decimal("30"),
        gross_amount=Decimal("60"),
        product_discount=Decimal("5"),
        explicit_net_amount=Decimal("54.50"),
    )
    assert result.export_amount == Decimal("54.50")


def test_invoice_discount_is_not_a_line_input():
    # By design calculate_line has no invoice-level discount parameter.
    result = calculate_line(
        case_quantity=Decimal("1"),
        units_per_case=24,
        explicit_unit_quantity=None,
        case_price=None,
        gross_amount=Decimal("60"),
        product_discount=None,
        explicit_net_amount=None,
    )
    assert result.export_amount == Decimal("60.00")
