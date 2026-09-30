from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path
from typing import Protocol

from app.models import Invoice
from app.services.storage import export_path


class ExportNotReadyError(RuntimeError):
    pass


class InvoiceExporter(Protocol):
    """Contract for downstream export formats."""

    def export(self, invoice: Invoice) -> Path:
        ...


def _require_ready(invoice: Invoice) -> None:
    if not invoice.validation or not invoice.validation.get("ready"):
        raise ExportNotReadyError("Invoice has unresolved review/validation issues")


def _format_quantity(value: Decimal) -> str:
    if value == value.to_integral_value():
        return str(int(value))
    return format(value.normalize(), "f")


class CsvExporter:
    """Current required three-column Scan2EDI export."""

    def export(self, invoice: Invoice) -> Path:
        _require_ready(invoice)
        path = export_path(invoice.id, "csv")
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["UPC Code", "Quantity", "Total Amount"])
            for line in invoice.lines:
                writer.writerow([
                    line.upc,
                    _format_quantity(Decimal(str(line.total_quantity))),
                    f"{Decimal(str(line.export_total)):.2f}",
                ])
        return path


def write_csv(invoice: Invoice) -> Path:
    return CsvExporter().export(invoice)
