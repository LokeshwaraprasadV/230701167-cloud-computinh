from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Eye ROI Analyzer for Diabetic Retinopathy"
    environment: str = "local"
    frontend_origin: str = "http://localhost:5173"

    local_storage_dir: str = "storage"
    local_db_json_path: str = "storage/db.json"

    azure_storage_connection_string: str = ""
    azure_blob_container_name: str = "retina-images"
    azure_blob_public_base_url: str = ""

    cosmos_mongo_uri: str = ""
    cosmos_db_name: str = "eye_roi_analyzer"
    cosmos_collection_name: str = "predictions"

    model_path: str = "app/models/dr_model.keras"

    reports_dir: str = "storage/reports"


settings = Settings()

