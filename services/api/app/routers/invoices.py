from __future__ import annotations

import logging
import time

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.db import get_db
from app.models import Invoice, InvoiceLine, VendorProductMapping
from app.schemas import ExtractedLine, InvoiceLineUpdate, InvoiceOut, InvoiceSummaryOut, InvoiceUpdate, LineMappingConfirm
from app.services.document_ai import (
    DocumentAIConfigurationError,
    DocumentAIExtractor,
    DocumentAIProcessingError,
)
from app.services.document_mapper import map_document
from app.services.exporters import ExportNotReadyError, write_csv
from app.services.mapping_service import add_history, find_mapping, normalize_description
from app.services.storage import store_invoice
from app.services.validation import validate_invoice
from app.services.vendor_rules import calculate_line, canonical_vendor_name

router = APIRouter(prefix="/invoices", tags=["invoices"])
logger = logging.getLogger("scan2edi.invoices")

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}


def _load_invoice(db: Session, invoice_id: str) -> Invoice:
    stmt = (
        select(Invoice)
        .options(selectinload(Invoice.lines))
        .where(Invoice.id == invoice_id)
    )
    invoice = db.scalar(stmt)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


def _apply_line_rules(db: Session, invoice: Invoice, line: InvoiceLine) -> None:
    extracted = ExtractedLine(
        confidence=line.confidence,
        vendor_sku=line.vendor_sku,
        description=line.description,
        printed_upc=line.printed_upc,
        case_quantity=line.case_quantity,
        units_per_case=line.units_per_case,
        direct_quantity=line.direct_quantity,
        price=line.price,
        base_amount=line.base_amount,
        deposit=line.deposit,
        discount=line.discount,
        sugar_tax=line.sugar_tax,
        line_total=line.line_total,
    )

    mapping = find_mapping(db, invoice.vendor or "", line.vendor_sku, line.description)
    mapped_units = mapping.units_per_case if mapping else None
    if mapping:
        line.upc = line.upc or mapping.upc
        if line.units_per_case is None and mapping.units_per_case is not None:
            line.units_per_case = mapping.units_per_case
            extracted.units_per_case = mapping.units_per_case

    calculated = calculate_line(invoice.vendor, extracted, mapped_units)
    line.total_quantity = calculated.total_quantity
    line.export_total = calculated.export_total

    reasons = list(calculated.reasons)
    if line.confidence is not None and line.confidence < settings.min_line_confidence:
        reasons.append(f"Low extraction confidence: {line.confidence:.2f}")
    if not line.upc:
        if line.printed_upc:
            reasons.append(f"Confirm suggested UPC {line.printed_upc}")
        else:
            reasons.append("UPC mapping is required")
    line.review_reasons = reasons
    line.needs_review = bool(reasons)


def _revalidate(db: Session, invoice: Invoice) -> None:
    for line in invoice.lines:
        _apply_line_rules(db, invoice, line)

    invoice.validation = validate_invoice(
        invoice.lines,
        vendor=invoice.vendor,
        reported_cases=invoice.reported_cases,
        reported_units=invoice.reported_units,
        invoice_total=invoice.invoice_total,
        invoice_discount=invoice.invoice_discount,
        invoice_tax=invoice.invoice_tax,
    )
    invoice.status = "ready" if invoice.validation["ready"] else "review"


@router.get("", response_model=list[InvoiceSummaryOut])
def list_invoices(db: Session = Depends(get_db)):
    return list(db.scalars(select(Invoice).order_by(Invoice.created_at.desc())).all())


@router.post("", response_model=InvoiceOut)
async def create_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    mime_type = file.content_type or "application/octet-stream"
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {mime_type}")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(contents) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Maximum upload size is {settings.max_upload_mb} MB")

    source_path = store_invoice(contents, file.filename or "invoice")
    invoice = Invoice(
        filename=file.filename or source_path.name,
        mime_type=mime_type,
        source_path=str(source_path),
        status="processing",
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    try:
        started = time.perf_counter()
        logger.info("Processing invoice %s with Google Document AI", invoice.filename)
        extractor = DocumentAIExtractor()
        document = await run_in_threadpool(extractor.process, contents, mime_type)
        extracted = map_document(document)
        logger.info(
            "Document AI completed invoice %s in %.2fs with %d product lines",
            invoice.id,
            time.perf_counter() - started,
            len(extracted.lines),
        )
    except DocumentAIConfigurationError as exc:
        invoice.status = "error"
        invoice.validation = {"ready": False, "issues": [str(exc)]}
        db.commit()
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except DocumentAIProcessingError as exc:
        invoice.status = "error"
        invoice.validation = {"ready": False, "issues": [str(exc)]}
        db.commit()
        raise HTTPException(status_code=502, detail=f"Document AI failed: {exc}") from exc

    invoice.vendor = canonical_vendor_name(extracted.vendor)
    invoice.invoice_number = extracted.invoice_number
    invoice.invoice_date = extracted.invoice_date
    invoice.reported_cases = extracted.reported_cases
    invoice.reported_units = extracted.reported_units
    invoice.invoice_subtotal = extracted.invoice_subtotal
    invoice.invoice_discount = extracted.invoice_discount
    invoice.invoice_deposit = extracted.invoice_deposit
    invoice.invoice_tax = extracted.invoice_tax
    invoice.invoice_total = extracted.invoice_total
    invoice.raw_extraction = extracted.raw

    for index, item in enumerate(extracted.lines, start=1):
        line = InvoiceLine(
            invoice_id=invoice.id,
            sequence=index,
            confidence=item.confidence,
            vendor_sku=item.vendor_sku,
            description=item.description,
            printed_upc=item.printed_upc,
            case_quantity=item.case_quantity,
            units_per_case=item.units_per_case,
            direct_quantity=item.direct_quantity,
            price=item.price,
            base_amount=item.base_amount,
            deposit=item.deposit,
            discount=item.discount,
            sugar_tax=item.sugar_tax,
            line_total=item.line_total,
        )
        db.add(line)

    db.flush()
    db.refresh(invoice)
    invoice = _load_invoice(db, invoice.id)
    _revalidate(db, invoice)
    db.commit()
    return _load_invoice(db, invoice.id)


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    return _load_invoice(db, invoice_id)


@router.get("/{invoice_id}/raw")
def get_raw_extraction(invoice_id: str, db: Session = Depends(get_db)):
    invoice = _load_invoice(db, invoice_id)
    return invoice.raw_extraction or {}


@router.patch("/{invoice_id}", response_model=InvoiceOut)
def update_invoice(
    invoice_id: str,
    payload: InvoiceUpdate,
    db: Session = Depends(get_db),
):
    invoice = _load_invoice(db, invoice_id)
    changes = payload.model_dump(exclude_unset=True)
    if "vendor" in changes:
        changes["vendor"] = canonical_vendor_name(changes["vendor"])
    for key, value in changes.items():
        setattr(invoice, key, value)
    _revalidate(db, invoice)
    db.commit()
    return _load_invoice(db, invoice_id)


@router.patch("/{invoice_id}/lines/{line_id}", response_model=InvoiceOut)
def update_invoice_line(
    invoice_id: str,
    line_id: str,
    payload: InvoiceLineUpdate,
    db: Session = Depends(get_db),
):
    invoice = _load_invoice(db, invoice_id)
    line = next((row for row in invoice.lines if row.id == line_id), None)
    if not line:
        raise HTTPException(status_code=404, detail="Invoice line not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(line, key, value)

    _revalidate(db, invoice)
    db.commit()
    return _load_invoice(db, invoice_id)


@router.post("/{invoice_id}/lines/{line_id}/mapping", response_model=InvoiceOut)
def confirm_line_mapping(
    invoice_id: str,
    line_id: str,
    payload: LineMappingConfirm,
    db: Session = Depends(get_db),
):
    invoice = _load_invoice(db, invoice_id)
    line = next((row for row in invoice.lines if row.id == line_id), None)
    if not line:
        raise HTTPException(status_code=404, detail="Invoice line not found")
    if not invoice.vendor:
        raise HTTPException(status_code=409, detail="Vendor must be known before a product mapping can be saved")

    normalized = normalize_description(line.description)
    mapping = None
    if line.vendor_sku:
        mapping = db.scalar(select(VendorProductMapping).where(
            VendorProductMapping.vendor_name == invoice.vendor,
            VendorProductMapping.vendor_sku == line.vendor_sku,
        ))
    if mapping is None:
        mapping = db.scalar(select(VendorProductMapping).where(
            VendorProductMapping.vendor_name == invoice.vendor,
            VendorProductMapping.normalized_description == normalized,
        ))
    if mapping:
        was_active = mapping.active
        mapping.vendor_sku = line.vendor_sku
        mapping.upc = payload.upc
        mapping.units_per_case = payload.units_per_case
        mapping.active = True
        add_history(db, mapping, "UPDATE" if was_active else "REACTIVATE")
    else:
        mapping = VendorProductMapping(
            vendor_name=invoice.vendor,
            vendor_sku=line.vendor_sku,
            normalized_description=normalized,
            upc=payload.upc,
            units_per_case=payload.units_per_case,
            active=True,
        )
        db.add(mapping)
        db.flush()
        add_history(db, mapping, "CREATE")

    line.upc = payload.upc
    if payload.units_per_case is not None:
        line.units_per_case = payload.units_per_case

    _revalidate(db, invoice)
    db.commit()
    return _load_invoice(db, invoice_id)


@router.post("/{invoice_id}/revalidate", response_model=InvoiceOut)
def revalidate(invoice_id: str, db: Session = Depends(get_db)):
    invoice = _load_invoice(db, invoice_id)
    _revalidate(db, invoice)
    db.commit()
    return _load_invoice(db, invoice_id)


@router.get("/{invoice_id}/export.csv")
def export_csv(invoice_id: str, db: Session = Depends(get_db)):
    invoice = _load_invoice(db, invoice_id)
    _revalidate(db, invoice)
    db.commit()
    try:
        path = write_csv(invoice)
    except ExportNotReadyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return FileResponse(path, media_type="text/csv", filename=f"scan2edi-{invoice_id}.csv")
