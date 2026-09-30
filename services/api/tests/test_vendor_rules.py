from decimal import Decimal

from app.schemas import ExtractedLine
from app.services.vendor_rules import calculate_line, vendor_family


def test_redbull_quantity_and_final_total():
    line = ExtractedLine(
        description="RED BULL 8.4OZ 4PK",
        case_quantity=Decimal("2"),
        units_per_case=12,
        line_total=Decimal("79.38"),
        deposit=Decimal("1.20"),
        discount=Decimal("7.50"),
    )
    result = calculate_line("Red Bull Distribution Company Inc", line)
    assert result.total_quantity == Decimal("24")
    assert result.export_total == Decimal("79.38")
    assert not result.reasons


def test_bjs_includes_deposit_and_subtracts_product_coupon():
    line = ExtractedLine(
        description="MONSTER 24PK",
        direct_quantity=Decimal("1"),
        base_amount=Decimal("42.48"),
        deposit=Decimal("1.20"),
        discount=Decimal("4.00"),
    )
    result = calculate_line("BJ's Wholesale Club", line)
    assert result.total_quantity == Decimal("1")
    assert result.export_total == Decimal("39.68")


def test_market_basket_uses_direct_quantity():
    line = ExtractedLine(
        description="BUBBA BURGER",
        direct_quantity=Decimal("4"),
        line_total=Decimal("51.96"),
    )
    result = calculate_line("Market Basket", line)
    assert result.total_quantity == Decimal("4")
    assert result.export_total == Decimal("51.96")


def test_paul_henry_return_supports_negative_values():
    line = ExtractedLine(
        description="Nabisco Golden Oreo Cakesters",
        direct_quantity=Decimal("-4"),
        line_total=Decimal("-5.76"),
    )
    result = calculate_line("Paul Henry Foods", line)
    assert result.total_quantity == Decimal("-4")
    assert result.export_total == Decimal("-5.76")
    assert not result.reasons


def test_missing_pack_size_requires_review():
    line = ExtractedLine(
        description="CASE PRODUCT",
        case_quantity=Decimal("3"),
        line_total=Decimal("81.00"),
    )
    result = calculate_line("GL Distribution", line)
    assert result.total_quantity is None
    assert any("Units per case" in reason for reason in result.reasons)


def test_vendor_family():
    assert vendor_family("Coca-Cola Northeast") == "coca_cola"
