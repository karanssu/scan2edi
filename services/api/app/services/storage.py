from pathlib import Path
import re
import uuid

from app.config import settings


def ensure_storage() -> None:
    settings.invoice_storage.mkdir(parents=True, exist_ok=True)
    settings.export_storage.mkdir(parents=True, exist_ok=True)


def safe_name(filename: str) -> str:
    base = Path(filename).name
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", base)
    return base or "invoice"


def store_invoice(contents: bytes, filename: str) -> Path:
    ensure_storage()
    path = settings.invoice_storage / f"{uuid.uuid4()}-{safe_name(filename)}"
    path.write_bytes(contents)
    return path


def export_path(invoice_id: str, suffix: str = "csv") -> Path:
    ensure_storage()
    return settings.export_storage / f"{invoice_id}.{suffix}"
