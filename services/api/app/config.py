from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Scan2EDI"
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://scan2edi:change-me@postgres:5432/scan2edi"

    invoice_storage_path: str = "/data/invoices"
    export_storage_path: str = "/data/exports"
    max_upload_mb: int = 25
    min_line_confidence: float = 0.75

    gcp_project_id: str = ""
    gcp_location: str = "us"
    document_ai_processor_id: str = ""
    document_ai_processor_version_id: str = ""
    google_application_credentials: str = "/run/secrets/gcp-service-account.json"

    @property
    def invoice_storage(self) -> Path:
        return Path(self.invoice_storage_path)

    @property
    def export_storage(self) -> Path:
        return Path(self.export_storage_path)


@lru_cache

def get_settings() -> Settings:
    return Settings()


settings = get_settings()
