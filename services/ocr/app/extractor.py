import json
import os

import httpx

from app.schemas import ExtractedInvoice


SYSTEM_PROMPT = """You extract vendor invoice data for Scan2EDI.
Return only schema-valid JSON. Never invent UPCs or product mappings.
A discount visually attached to a product belongs in product_discount.
A general discount in the invoice totals/summary belongs only in invoice_level_discount.
Do not distribute a general invoice discount across products.
If a line already shows the final/net product amount, put it in explicit_net_amount.
case_quantity means number of cases. units_per_case means individual units in one case.
explicit_unit_quantity is only for invoices that directly state individual unit quantity.
"""


class LocalInvoiceExtractor:
    def __init__(self) -> None:
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

    def extract_from_text(self, document_text: str) -> ExtractedInvoice:
        schema = ExtractedInvoice.model_json_schema()
        payload = {
            "model": self.model,
            "stream": False,
            "format": schema,
            "options": {"temperature": 0},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract this invoice.\n\n{document_text}"},
            ],
        }

        try:
            response = httpx.post(
                f"{self.ollama_url}/api/chat",
                json=payload,
                timeout=180,
            )
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Local Ollama service is not reachable at {self.ollama_url}: {exc}"
            ) from exc

        if response.is_error:
            try:
                detail = response.json().get("error") or response.text
            except Exception:
                detail = response.text
            raise RuntimeError(
                f"Local Ollama returned HTTP {response.status_code}: {detail}"
            )

        try:
            content = response.json()["message"]["content"]
            return ExtractedInvoice.model_validate_json(content)
        except Exception as exc:
            raise RuntimeError(
                f"Local model returned an invalid invoice schema: {exc}"
            ) from exc


def paddle_document_text(path: str) -> str:
    """Use PaddleOCR-VL locally and return a textual representation."""
    try:
        from paddleocr import PaddleOCRVL
    except ImportError as exc:
        raise RuntimeError(
            "PaddleOCR-VL is not installed in the OCR container. "
            "Rebuild the OCR image after installing PaddlePaddle and "
            "paddleocr[doc-parser]."
        ) from exc

    try:
        pipeline = PaddleOCRVL()
        output = list(pipeline.predict(path))
    except Exception as exc:
        raise RuntimeError(f"PaddleOCR-VL failed to process the invoice: {exc}") from exc

    parts: list[str] = []
    for page in output:
        data = getattr(page, "json", None)
        if callable(data):
            data = data()
        if data is not None:
            parts.append(json.dumps(data, default=str))
        else:
            parts.append(str(page))
    return "\n\n".join(parts)
