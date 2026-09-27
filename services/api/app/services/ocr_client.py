from pathlib import Path

import httpx

from app.core.config import get_settings
from app.schemas.domain import OCRInvoiceResult


def extract_invoice(path: Path) -> OCRInvoiceResult:
    settings = get_settings()
    with path.open("rb") as handle:
        response = httpx.post(
            f"{settings.ocr_service_url.rstrip('/')}/extract",
            files={"file": (path.name, handle, "application/octet-stream")},
            timeout=240,
        )
    response.raise_for_status()
    return OCRInvoiceResult.model_validate(response.json())
