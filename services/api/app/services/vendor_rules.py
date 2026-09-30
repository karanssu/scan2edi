from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import re

from app.schemas import ExtractedLine

ZERO = Decimal("0.00")
CENT = Decimal("0.01")


def money(value: Decimal | None) -> Decimal | None:
    return value.quantize(CENT, rounding=ROUND_HALF_UP) if value is not None else None


def vendor_family(vendor: str | None) -> str:
    value = (vendor or "").upper()
    value = re.sub(r"[^A-Z0-9]+", " ", value)
    if "RED BULL" in value:
        return "redbull"
    if "POLAR" in value:
        return "polar"
    if "BJ" in value and ("WHOLESALE" in value or "BJS" in value or "BJ S" in value):
        return "bjs"
    if "MARKET BASKET" in value:
        return "market_basket"
    if "PAUL HENRY" in value:
        return "paul_henry"
    if "GL DIST" in value or "G L DIST" in value:
        return "gl_distribution"
    if "COCA COLA" in value or "COKE" in value:
        return "coca_cola"
    return "generic"


def canonical_vendor_name(vendor: str | None) -> str | None:
    if not vendor:
        return None
    family = vendor_family(vendor)
    names = {
        "redbull": "Red Bull Distribution Company",
        "polar": "Polar Beverages",
        "bjs": "BJ's Wholesale Club",
        "market_basket": "Market Basket",
        "paul_henry": "Paul Henry Foods",
        "gl_distribution": "GL Distribution",
        "coca_cola": "Coca-Cola",
    }
    return names.get(family, vendor.strip())


@dataclass
class CalculatedLine:
    total_quantity: Decimal | None
    export_total: Decimal | None
    reasons: list[str]

    @property
    def needs_review(self) -> bool:
        return bool(self.reasons)


def _quantity(line: ExtractedLine, mapped_units_per_case: int | None, prefer_direct: bool = False) -> tuple[Decimal | None, list[str]]:
    reasons: list[str] = []
    if prefer_direct and line.direct_quantity is not None:
        return line.direct_quantity, reasons

    units = line.units_per_case or mapped_units_per_case
    if line.case_quantity is not None and units is not None:
        return line.case_quantity * Decimal(units), reasons

    if line.direct_quantity is not None:
        return line.direct_quantity, reasons

    if line.case_quantity is not None and units is None:
        reasons.append("Units per case is required for this case quantity")
        return None, reasons

    reasons.append("Quantity could not be resolved")
    return None, reasons


def calculate_line(vendor: str | None, line: ExtractedLine, mapped_units_per_case: int | None = None) -> CalculatedLine:
    family = vendor_family(vendor)
    reasons: list[str] = []

    if family in {"market_basket", "paul_henry"}:
        quantity, q_reasons = _quantity(line, mapped_units_per_case, prefer_direct=True)
    else:
        quantity, q_reasons = _quantity(line, mapped_units_per_case)
    reasons.extend(q_reasons)
    if quantity is not None and quantity != quantity.to_integral_value():
        reasons.append(f"Calculated selling-unit quantity is not a whole number: {quantity}")

    export_total: Decimal | None
    if family in {"redbull", "polar", "market_basket", "paul_henry", "gl_distribution"}:
        export_total = money(line.line_total)
        if export_total is None:
            reasons.append("Final line amount is missing")
    elif family == "bjs":
        if line.base_amount is not None:
            export_total = money(
                line.base_amount + (line.deposit or ZERO) - (line.discount or ZERO)
            )
        elif line.line_total is not None:
            export_total = money(line.line_total)
        else:
            export_total = None
            reasons.append("BJ's product amount is missing")
    elif family == "coca_cola":
        if line.line_total is not None:
            export_total = money(line.line_total)
        elif line.base_amount is not None:
            export_total = money(
                line.base_amount + (line.deposit or ZERO) - (line.discount or ZERO)
            )
        else:
            export_total = None
            reasons.append("Product total is missing")
    else:
        if line.line_total is not None:
            export_total = money(line.line_total)
        elif line.base_amount is not None:
            export_total = money(line.base_amount)
            if line.deposit not in (None, ZERO) or line.discount not in (None, ZERO):
                reasons.append("Unknown vendor has product adjustments; review total")
        else:
            export_total = None
            reasons.append("Product total is missing")

    if family == "paul_henry" and quantity is not None and export_total is not None:
        if (quantity < 0) != (export_total < 0):
            reasons.append("Return quantity and amount signs do not match")

    return CalculatedLine(quantity, export_total, reasons)
