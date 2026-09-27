import os
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.extractor import LocalInvoiceExtractor, paddle_document_text
from app.schemas import ExtractedInvoice

app = FastAPI(title="Scan2EDI Local OCR", version="0.1.0")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "scan2edi-ocr",
        "engine": os.getenv("OCR_ENGINE", "paddle"),
    }


@app.post("/extract", response_model=ExtractedInvoice)
def extract(file: UploadFile = File(...)):
    suffix = Path(file.filename or "invoice.bin").suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        path = tmp.name

    try:
        document_text = paddle_document_text(path)
        return LocalInvoiceExtractor().extract_from_text(document_text)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        Path(path).unlink(missing_ok=True)
