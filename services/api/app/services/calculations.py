from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


CENT = Decimal("0.01")


@dataclass(frozen=True)
class LineCalculation:
    total_quantity: Decimal | None
    gross_amount: Decimal | None
    export_amount: Decimal | None
    reason: str | None


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def calculate_line(
    *,
    case_quantity: Decimal | None,
    units_per_case: int | None,
    explicit_unit_quantity: Decimal | None,
    case_price: Decimal | None,
    gross_amount: Decimal | None,
    product_discount: Decimal | None,
    explicit_net_amount: Decimal | None,
) -> LineCalculation:
    """Apply Scan2EDI export rules.

    Quantity is total individual units. A product-specific discount reduces the
    product's exported amount. Invoice-level discounts are intentionally absent
    from this function because they never change product export amounts.
    """
    quantity: Decimal | None = None
    if case_quantity is not None and units_per_case is not None:
        quantity = case_quantity * Decimal(units_per_case)
    elif explicit_unit_quantity is not None:
        quantity = explicit_unit_quantity

    resolved_gross = gross_amount
    if resolved_gross is None and case_quantity is not None and case_price is not None:
        resolved_gross = money(case_quantity * case_price)

    if explicit_net_amount is not None:
        export_amount = money(explicit_net_amount)
    elif resolved_gross is not None:
        export_amount = money(resolved_gross - (product_discount or Decimal("0")))
    else:
        export_amount = None

    reasons: list[str] = []
    if quantity is None:
        reasons.append("total quantity cannot be determined")
    if export_amount is None:
        reasons.append("product total amount cannot be determined")
    elif export_amount < 0:
        reasons.append("product total amount is negative")

    return LineCalculation(
        total_quantity=quantity,
        gross_amount=money(resolved_gross) if resolved_gross is not None else None,
        export_amount=export_amount,
        reason="; ".join(reasons) or None,
    )
