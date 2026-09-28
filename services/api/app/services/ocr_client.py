from pathlib import Path

import httpx

from app.core.config import get_settings
from app.schemas.domain import OCRInvoiceResult


class OCRServiceError(RuntimeError):
    pass


def extract_invoice(path: Path) -> OCRInvoiceResult:
    settings = get_settings()
    url = f"{settings.ocr_service_url.rstrip('/')}/extract"

    try:
        with path.open("rb") as handle:
            response = httpx.post(
                url,
                files={"file": (path.name, handle, "application/octet-stream")},
                timeout=httpx.Timeout(
                    settings.ocr_request_timeout_seconds,
                    connect=10.0,
                ),
            )
    except httpx.RequestError as exc:
        raise OCRServiceError(f"Could not reach local OCR service at {url}: {exc}") from exc

    if response.is_error:
        try:
            body = response.json()
            detail = body.get("detail", body)
        except Exception:
            detail = response.text
        raise OCRServiceError(
            f"OCR service returned HTTP {response.status_code}: {detail}"
        )

    try:
        return OCRInvoiceResult.model_validate(response.json())
    except Exception as exc:
        raise OCRServiceError(f"OCR service returned an invalid response: {exc}") from exc
