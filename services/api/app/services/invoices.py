from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.entities import Invoice, InvoiceLine, VendorProductMapping
from app.schemas.domain import InvoiceCreate
from app.services.calculations import calculate_line
from app.services.mapping import find_mapping


def build_invoice(db: Session, payload: InvoiceCreate) -> Invoice:
    invoice = Invoice(
        vendor_id=payload.vendor_id,
        invoice_number=payload.invoice_number,
        subtotal=payload.subtotal,
        invoice_level_discount=payload.invoice_level_discount,
        invoice_total=payload.invoice_total,
        status="review",
    )
    db.add(invoice)
    db.flush()

    for index, source in enumerate(payload.lines, start=1):
        mapping = find_mapping(
            db,
            vendor_id=payload.vendor_id,
            vendor_sku=source.vendor_sku,
            description=source.description,
            units_per_case=source.units_per_case,
        )

        units_per_case = source.units_per_case or (mapping.units_per_case if mapping else None)
        calc = calculate_line(
            case_quantity=source.case_quantity,
            units_per_case=units_per_case,
            explicit_unit_quantity=source.explicit_unit_quantity,
            case_price=source.case_price,
            gross_amount=source.gross_amount,
            product_discount=source.product_discount,
            explicit_net_amount=source.explicit_net_amount,
        )

        reasons: list[str] = []
        if mapping is None:
            reasons.append("UPC mapping required")
        if calc.reason:
            reasons.append(calc.reason)

        line = InvoiceLine(
            invoice_id=invoice.id,
            line_number=index,
            description=source.description,
            vendor_sku=source.vendor_sku,
            product_id=mapping.product_id if mapping else None,
            case_quantity=source.case_quantity,
            units_per_case=units_per_case,
            explicit_unit_quantity=source.explicit_unit_quantity,
            total_quantity=calc.total_quantity,
            case_price=source.case_price,
            gross_amount=calc.gross_amount,
            product_discount=source.product_discount,
            explicit_net_amount=source.explicit_net_amount,
            export_amount=calc.export_amount,
            needs_review=bool(reasons),
            review_reason="; ".join(reasons) or None,
        )
        db.add(line)

    db.flush()
    refresh_invoice_status(invoice)
    return invoice


def refresh_invoice_status(invoice: Invoice) -> None:
    invoice.status = "review" if any(line.needs_review for line in invoice.lines) else "ready"
