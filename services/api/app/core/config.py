from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Scan2EDI"
    app_env: str = "development"
    database_url: str = "sqlite:///./scan2edi.db"
    invoice_storage_path: str = "./storage/invoices"
    export_storage_path: str = "./storage/exports"
    ocr_service_url: str = "http://localhost:8080"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
