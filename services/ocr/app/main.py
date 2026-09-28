import logging
import os
import shutil
import tempfile
import time
from pathlib import Path

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile

from app.extractor import LocalInvoiceExtractor, paddle_document_text
from app.schemas import ExtractedInvoice

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("scan2edi.ocr")

app = FastAPI(title="Scan2EDI Local OCR", version="0.3.0")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "scan2edi-ocr",
        "engine": os.getenv("OCR_ENGINE", "paddle"),
    }


@app.get("/ready")
def ready():
    """Verify that both local inference stages are actually usable."""
    problems: list[str] = []

    try:
        import paddleocr  # noqa: F401
    except Exception as exc:
        problems.append(f"PaddleOCR is unavailable: {exc}")

    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    try:
        response = httpx.get(f"{ollama_url}/api/tags", timeout=5)
        response.raise_for_status()
        installed = {
            item.get("name")
            for item in response.json().get("models", [])
            if item.get("name")
        }
        if model not in installed:
            problems.append(
                f"Ollama model '{model}' is not installed. "
                f"Run: docker compose exec ollama ollama pull {model}"
            )
    except Exception as exc:
        problems.append(f"Ollama is unavailable at {ollama_url}: {exc}")

    if problems:
        raise HTTPException(status_code=503, detail=problems)

    return {
        "status": "ready",
        "service": "scan2edi-ocr",
        "model": model,
    }


@app.post("/extract", response_model=ExtractedInvoice)
def extract(file: UploadFile = File(...)):
    suffix = Path(file.filename or "invoice.bin").suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        path = tmp.name

    started = time.monotonic()
    logger.info("Received invoice %s for local processing", file.filename)

    try:
        document_text = paddle_document_text(path)
        if not document_text.strip():
            raise RuntimeError("PaddleOCR returned no document content for this invoice.")

        result = LocalInvoiceExtractor().extract_from_text(document_text)
        logger.info(
            "Invoice %s fully processed locally in %.1fs",
            file.filename,
            time.monotonic() - started,
        )
        return result
    except RuntimeError as exc:
        logger.exception("Local invoice processing failed for %s", file.filename)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Invoice extraction failed for %s", file.filename)
        raise HTTPException(
            status_code=422,
            detail=f"Invoice extraction failed: {type(exc).__name__}: {exc}",
        ) from exc
    finally:
        Path(path).unlink(missing_ok=True)
