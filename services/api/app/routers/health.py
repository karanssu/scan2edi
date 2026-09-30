from pathlib import Path

from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    credentials = Path(settings.google_application_credentials)
    return {
        "status": "ok",
        "service": "scan2edi-api",
        "version": "2.0.0",
        "document_ai": {
            "configured": bool(settings.gcp_project_id and settings.document_ai_processor_id),
            "project_id": settings.gcp_project_id or None,
            "location": settings.gcp_location,
            "processor_id_configured": bool(settings.document_ai_processor_id),
            "processor_version_pinned": bool(settings.document_ai_processor_version_id),
            "credentials_file_present": credentials.exists(),
        },
    }
