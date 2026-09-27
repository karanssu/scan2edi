import csv
import io
from decimal import Decimal

from app.models.entities import Invoice


def format_quantity(value: Decimal) -> str:
    if value == value.to_integral_value():
        return str(int(value))
    return format(value.normalize(), "f")


def invoice_to_csv(invoice: Invoice) -> str:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["UPC Code", "Quantity", "Total Amount"])

    for line in sorted(invoice.lines, key=lambda item: item.line_number):
        if line.needs_review or not line.product or line.total_quantity is None or line.export_amount is None:
            raise ValueError(f"Invoice line {line.line_number} is not ready for export")
        writer.writerow([
            line.product.upc,
            format_quantity(line.total_quantity),
            f"{line.export_amount:.2f}",
        ])

    return output.getvalue()
