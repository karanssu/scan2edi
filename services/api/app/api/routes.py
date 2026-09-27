from pathlib import Path

import httpx

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.entities import Invoice, InvoiceLine, Product, Vendor, VendorProductMapping
from app.core.config import get_settings
from app.schemas.domain import (
    InvoiceCreate,
    InvoiceLineOut,
    InvoiceOut,
    ManualMapRequest,
    MappingCreate,
    MappingOut,
    VendorCreate,
    VendorOut,
)
from app.services.calculations import calculate_line
from app.services.export import invoice_to_csv
from app.services.invoices import build_invoice, refresh_invoice_status
from app.services.mapping import get_or_create_product
from app.services.normalization import normalize_description
from app.services.ocr_client import extract_invoice

router = APIRouter()


def invoice_query():
    return select(Invoice).options(
        selectinload(Invoice.lines).selectinload(InvoiceLine.product)
    )


def serialize_invoice(invoice: Invoice) -> InvoiceOut:
    return InvoiceOut(
        id=invoice.id,
        vendor_id=invoice.vendor_id,
        invoice_number=invoice.invoice_number,
        status=invoice.status,
        subtotal=invoice.subtotal,
        invoice_level_discount=invoice.invoice_level_discount,
        invoice_total=invoice.invoice_total,
        lines=[
            InvoiceLineOut(
                id=line.id,
                line_number=line.line_number,
                description=line.description,
                vendor_sku=line.vendor_sku,
                upc=line.product.upc if line.product else None,
                case_quantity=line.case_quantity,
                units_per_case=line.units_per_case,
                total_quantity=line.total_quantity,
                gross_amount=line.gross_amount,
                product_discount=line.product_discount,
                export_amount=line.export_amount,
                needs_review=line.needs_review,
                review_reason=line.review_reason,
            )
            for line in sorted(invoice.lines, key=lambda item: item.line_number)
        ],
    )


@router.get("/health")
def health():
    return {"status": "ok", "service": "scan2edi-api"}


@router.post("/vendors", response_model=VendorOut, status_code=201)
def create_vendor(payload: VendorCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(Vendor).where(Vendor.name == payload.name))
    if existing:
        return existing
    vendor = Vendor(name=payload.name)
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


@router.get("/vendors", response_model=list[VendorOut])
def list_vendors(db: Session = Depends(get_db)):
    return list(db.scalars(select(Vendor).order_by(Vendor.name)))


@router.post("/mappings", response_model=MappingOut, status_code=201)
def create_mapping(payload: MappingCreate, db: Session = Depends(get_db)):
    vendor = db.get(Vendor, payload.vendor_id)
    if not vendor:
        raise HTTPException(404, "Vendor not found")

    product = get_or_create_product(db, payload.upc, payload.canonical_name)
    mapping = VendorProductMapping(
        vendor_id=payload.vendor_id,
        product_id=product.id,
        vendor_sku=payload.vendor_sku,
        vendor_description=payload.vendor_description,
        normalized_description=normalize_description(payload.vendor_description),
        units_per_case=payload.units_per_case,
    )
    db.add(mapping)
    db.commit()
    db.refresh(mapping)
    return MappingOut(
        id=mapping.id,
        vendor_id=mapping.vendor_id,
        product_id=mapping.product_id,
        vendor_sku=mapping.vendor_sku,
        vendor_description=mapping.vendor_description,
        normalized_description=mapping.normalized_description,
        units_per_case=mapping.units_per_case,
        upc=product.upc,
        canonical_name=product.canonical_name,
    )


@router.get("/mappings", response_model=list[MappingOut])
def list_mappings(db: Session = Depends(get_db)):
    rows = db.execute(
        select(VendorProductMapping, Product)
        .join(Product, Product.id == VendorProductMapping.product_id)
        .order_by(VendorProductMapping.vendor_description)
    ).all()
    return [
        MappingOut(
            id=m.id,
            vendor_id=m.vendor_id,
            product_id=m.product_id,
            vendor_sku=m.vendor_sku,
            vendor_description=m.vendor_description,
            normalized_description=m.normalized_description,
            units_per_case=m.units_per_case,
            upc=p.upc,
            canonical_name=p.canonical_name,
        )
        for m, p in rows
    ]


@router.post("/invoices/scan", response_model=InvoiceOut, status_code=201)
def scan_invoice(
    file: UploadFile = File(...),
    vendor_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    allowed = {".png", ".jpg", ".jpeg", ".webp", ".pdf"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(415, "Supported invoice files: PNG, JPG, JPEG, WEBP, PDF")

    settings = get_settings()
    storage = Path(settings.invoice_storage_path)
    storage.mkdir(parents=True, exist_ok=True)

    import uuid
    stored_name = f"{uuid.uuid4()}{suffix}"
    destination = storage / stored_name
    max_bytes = 25 * 1024 * 1024
    written = 0
    try:
        with destination.open("wb") as output:
            while chunk := file.file.read(1024 * 1024):
                written += len(chunk)
                if written > max_bytes:
                    raise HTTPException(413, "Invoice file exceeds 25 MB")
                output.write(chunk)

        try:
            extracted = extract_invoice(destination)
        except httpx.HTTPError as exc:
            raise HTTPException(502, f"Local OCR service failed: {exc}") from exc

        vendor = db.get(Vendor, vendor_id) if vendor_id else None
        if vendor_id and not vendor:
            raise HTTPException(404, "Vendor not found")
        if vendor is None and extracted.vendor_name:
            vendor = db.scalar(
                select(Vendor).where(Vendor.name.ilike(extracted.vendor_name.strip()))
            )
        if vendor is None:
            raise HTTPException(409, "Vendor could not be matched. Select the vendor and scan again.")

        payload = InvoiceCreate(
            vendor_id=vendor.id,
            invoice_number=extracted.invoice_number,
            subtotal=extracted.subtotal,
            invoice_level_discount=extracted.invoice_level_discount,
            invoice_total=extracted.invoice_total,
            lines=extracted.lines,
        )
        invoice = build_invoice(db, payload)
        invoice.source_filename = stored_name
        db.commit()
        invoice = db.scalar(invoice_query().where(Invoice.id == invoice.id))
        return serialize_invoice(invoice)
    except Exception:
        if not destination.exists():
            raise
        # Keep successfully persisted invoices only. Failed scans should not leave
        # sensitive orphan files behind.
        if 'invoice' not in locals():
            destination.unlink(missing_ok=True)
        raise


@router.get("/invoices", response_model=list[InvoiceOut])
def list_invoices(db: Session = Depends(get_db)):
    invoices = db.scalars(invoice_query().order_by(Invoice.created_at.desc())).unique().all()
    return [serialize_invoice(invoice) for invoice in invoices]


@router.post("/invoices", response_model=InvoiceOut, status_code=201)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
    if not db.get(Vendor, payload.vendor_id):
        raise HTTPException(404, "Vendor not found")
    invoice = build_invoice(db, payload)
    db.commit()
    invoice = db.scalar(invoice_query().where(Invoice.id == invoice.id))
    return serialize_invoice(invoice)


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    invoice = db.scalar(invoice_query().where(Invoice.id == invoice_id))
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    return serialize_invoice(invoice)


@router.post("/invoices/{invoice_id}/lines/{line_id}/map", response_model=InvoiceOut)
def map_invoice_line(invoice_id: str, line_id: str, payload: ManualMapRequest, db: Session = Depends(get_db)):
    invoice = db.scalar(invoice_query().where(Invoice.id == invoice_id))
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    line = next((item for item in invoice.lines if item.id == line_id), None)
    if not line:
        raise HTTPException(404, "Invoice line not found")

    product = get_or_create_product(db, payload.upc, payload.canonical_name)
    mapping = VendorProductMapping(
        vendor_id=invoice.vendor_id,
        product_id=product.id,
        vendor_sku=line.vendor_sku,
        vendor_description=line.description,
        normalized_description=normalize_description(line.description),
        units_per_case=payload.units_per_case,
    )
    db.add(mapping)

    line.product_id = product.id
    line.units_per_case = line.units_per_case or payload.units_per_case
    calc = calculate_line(
        case_quantity=line.case_quantity,
        units_per_case=line.units_per_case,
        explicit_unit_quantity=line.explicit_unit_quantity,
        case_price=line.case_price,
        gross_amount=line.gross_amount,
        product_discount=line.product_discount,
        explicit_net_amount=line.explicit_net_amount,
    )
    line.total_quantity = calc.total_quantity
    line.gross_amount = calc.gross_amount
    line.export_amount = calc.export_amount
    line.needs_review = calc.reason is not None
    line.review_reason = calc.reason
    db.flush()
    refresh_invoice_status(invoice)
    db.commit()

    invoice = db.scalar(invoice_query().where(Invoice.id == invoice_id))
    return serialize_invoice(invoice)


@router.get("/invoices/{invoice_id}/export.csv")
def export_invoice(invoice_id: str, db: Session = Depends(get_db)):
    invoice = db.scalar(invoice_query().where(Invoice.id == invoice_id))
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    try:
        body = invoice_to_csv(invoice)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    filename = f"scan2edi-{invoice.invoice_number or invoice.id}.csv"
    return Response(
        content=body,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
