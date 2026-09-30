from __future__ import annotations

from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import GoogleAPIError
from google.cloud import documentai_v1 as documentai

from app.config import settings


class DocumentAIConfigurationError(RuntimeError):
    pass


class DocumentAIProcessingError(RuntimeError):
    pass


class DocumentAIExtractor:
    def __init__(self) -> None:
        if not settings.gcp_project_id or not settings.document_ai_processor_id:
            raise DocumentAIConfigurationError(
                "GCP_PROJECT_ID and DOCUMENT_AI_PROCESSOR_ID must be configured"
            )

        options = ClientOptions(
            api_endpoint=f"{settings.gcp_location}-documentai.googleapis.com"
        )
        self.client = documentai.DocumentProcessorServiceClient(client_options=options)

    def _processor_name(self) -> str:
        if settings.document_ai_processor_version_id:
            return self.client.processor_version_path(
                settings.gcp_project_id,
                settings.gcp_location,
                settings.document_ai_processor_id,
                settings.document_ai_processor_version_id,
            )
        return self.client.processor_path(
            settings.gcp_project_id,
            settings.gcp_location,
            settings.document_ai_processor_id,
        )

    def process(self, content: bytes, mime_type: str) -> documentai.Document:
        raw_document = documentai.RawDocument(content=content, mime_type=mime_type)
        request = documentai.ProcessRequest(
            name=self._processor_name(),
            raw_document=raw_document,
        )
        try:
            result = self.client.process_document(request=request)
        except GoogleAPIError as exc:
            raise DocumentAIProcessingError(str(exc)) from exc
        return result.document
