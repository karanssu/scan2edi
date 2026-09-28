import json
import logging
import os
import threading
import time
from functools import lru_cache

import httpx

from app.schemas import ExtractedInvoice


logger = logging.getLogger("scan2edi.ocr")
_paddle_predict_lock = threading.Lock()

SYSTEM_PROMPT = """You extract vendor invoice data for Scan2EDI.
Return only schema-valid JSON. Never invent UPCs or product mappings.
A discount visually attached to a product belongs in product_discount.
A general discount in the invoice totals/summary belongs only in invoice_level_discount.
Do not distribute a general invoice discount across products.
If a line already shows the final/net product amount, put it in explicit_net_amount.
case_quantity means number of cases. units_per_case means individual units in one case.
explicit_unit_quantity is only for invoices that directly state individual unit quantity.
For every optional field that is missing or unknown, return JSON null. Never return an empty string for numeric fields.
"""


class LocalInvoiceExtractor:
    def __init__(self) -> None:
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
        self.model = os.getenv("OLLAMA_MODEL", "qwen3:4b-instruct-2507-q4_K_M")
        self.timeout_seconds = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "600"))

    def extract_from_text(self, document_text: str) -> ExtractedInvoice:
        schema = ExtractedInvoice.model_json_schema()
        payload = {
            "model": self.model,
            "stream": False,
            "format": schema,
            "keep_alive": "10m",
            "options": {"temperature": 0},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract this invoice.\n\n{document_text}"},
            ],
        }

        logger.info(
            "Starting local LLM extraction with %s (%d document characters)",
            self.model,
            len(document_text),
        )
        started = time.monotonic()

        try:
            response = httpx.post(
                f"{self.ollama_url}/api/chat",
                json=payload,
                timeout=httpx.Timeout(self.timeout_seconds, connect=10.0),
            )
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Local Ollama request failed at {self.ollama_url}: {exc}"
            ) from exc

        logger.info("Local LLM extraction finished in %.1fs", time.monotonic() - started)

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


@lru_cache(maxsize=1)
def get_paddle_pipeline():
    """Load a CPU-friendly PP-StructureV3 pipeline once per OCR container."""
    try:
        from paddleocr import PPStructureV3
    except ImportError as exc:
        raise RuntimeError(
            "PP-StructureV3 is not installed in the OCR container. "
            "Rebuild the OCR image with PaddleOCR document parsing dependencies."
        ) from exc

    cpu_threads = max(1, int(os.getenv("OCR_CPU_THREADS", "4")))
    logger.info(
        "Loading lightweight PP-StructureV3 pipeline into memory (%d CPU threads)",
        cpu_threads,
    )
    started = time.monotonic()
    try:
        pipeline = PPStructureV3(
            device="cpu",
            enable_mkldnn=True,
            cpu_threads=cpu_threads,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            use_formula_recognition=False,
            use_seal_recognition=False,
            use_chart_recognition=False,
            use_table_recognition=True,
            text_detection_model_name="PP-OCRv5_mobile_det",
            text_recognition_model_name="en_PP-OCRv4_mobile_rec",
            layout_detection_model_name="PP-DocLayout-S",
            wired_table_structure_recognition_model_name="SLANet_plus",
            wireless_table_structure_recognition_model_name="SLANet_plus",
        )
    except Exception as exc:
        raise RuntimeError(f"Could not initialize PP-StructureV3: {exc}") from exc

    logger.info("PP-StructureV3 pipeline loaded in %.1fs", time.monotonic() - started)
    return pipeline


def _page_markdown_text(page) -> str | None:
    """Return human-readable Markdown text from a Paddle document result."""
    markdown = getattr(page, "markdown", None)
    if callable(markdown):
        markdown = markdown()

    if not isinstance(markdown, dict):
        return None

    value = markdown.get("markdown_texts")
    if value is None:
        value = markdown.get("text")

    if isinstance(value, str):
        return value.strip() or None

    if isinstance(value, (list, tuple)):
        text = "\n".join(str(item) for item in value if item).strip()
        return text or None

    return str(value).strip() if value else None


def _page_json(page) -> dict:
    data = getattr(page, "json", None)
    if callable(data):
        data = data()
    return data if isinstance(data, dict) else {}


def _result_body(data: dict) -> dict:
    # Paddle result objects commonly wrap the actual prediction under `res`.
    body = data.get("res")
    return body if isinstance(body, dict) else data


def _raw_ocr_text(page) -> str | None:
    """Extract recognized text directly from PP-StructureV3 JSON as a fallback."""
    body = _result_body(_page_json(page))
    parts: list[str] = []

    overall = body.get("overall_ocr_res")
    if isinstance(overall, dict):
        rec_texts = overall.get("rec_texts")
        if isinstance(rec_texts, (list, tuple)):
            parts.extend(str(item).strip() for item in rec_texts if str(item).strip())

    # Parsing blocks often retain table/text ordering better than raw OCR.
    parsing = body.get("parsing_res_list")
    if isinstance(parsing, list):
        block_parts = []
        for block in parsing:
            if isinstance(block, dict):
                content = block.get("block_content")
                if content and str(content).strip():
                    block_parts.append(str(content).strip())
        if block_parts:
            parts.extend(block_parts)

    # Include recognized table cell text if it adds information not present above.
    tables = body.get("table_res_list")
    if isinstance(tables, list):
        for table in tables:
            if not isinstance(table, dict):
                continue
            table_ocr = table.get("table_ocr_pred")
            if isinstance(table_ocr, dict):
                rec_texts = table_ocr.get("rec_texts")
                if isinstance(rec_texts, (list, tuple)):
                    parts.extend(str(item).strip() for item in rec_texts if str(item).strip())

    if not parts:
        return None

    # Preserve order while removing exact duplicates.
    unique_parts = list(dict.fromkeys(parts))
    text = "\n".join(unique_parts).strip()
    return text or None


def _best_page_text(page) -> str | None:
    markdown_text = _page_markdown_text(page) or ""
    raw_text = _raw_ocr_text(page) or ""

    # Markdown can occasionally contain only a title/heading even though the
    # global OCR result contains the full invoice. Prefer the richer result.
    if len(raw_text) > len(markdown_text) * 1.5 and len(raw_text) > 100:
        return raw_text
    return markdown_text or raw_text or None

def paddle_document_text(path: str) -> str:
    """Run lightweight PP-StructureV3 locally and return invoice Markdown/text."""
    pipeline = get_paddle_pipeline()

    logger.info("Starting PP-StructureV3 inference for %s", path)
    started = time.monotonic()
    try:
        # Guard the cached pipeline because Paddle inference objects are not
        # guaranteed to be safe for concurrent predict() calls.
        with _paddle_predict_lock:
            output = list(pipeline.predict(path))
    except Exception as exc:
        raise RuntimeError(f"PP-StructureV3 failed to process the invoice: {exc}") from exc

    logger.info("PP-StructureV3 inference finished in %.1fs", time.monotonic() - started)

    parts: list[str] = []
    for page in output:
        text = _best_page_text(page)
        if text:
            parts.append(text)

    document_text = "\n\n".join(parts).strip()
    logger.info("Prepared %d characters of invoice text for local LLM", len(document_text))
    logger.info("OCR text preview: %r", document_text[:500])

    if len(document_text) < 100:
        raise RuntimeError(
            "OCR recognized too little invoice text "
            f"({len(document_text)} characters). Check image quality/orientation or OCR settings."
        )

    return document_text
