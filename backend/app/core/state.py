from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.db.prediction_store import build_prediction_store
from app.services.model_service import get_default_model
from app.storage.blob_storage import BlobStorage, LocalBlobFallback


@dataclass
class AppState:
    blob: Any
    store: Any
    model: Any


def build_app_state(*, settings) -> AppState:
    if (settings.azure_storage_connection_string or "").strip():
        blob = BlobStorage(
            connection_string=settings.azure_storage_connection_string,
            container_name=settings.azure_blob_container_name,
            public_base_url=settings.azure_blob_public_base_url,
        )
    else:
        blob = LocalBlobFallback(base_dir=settings.local_storage_dir)

    store = build_prediction_store(
        cosmos_mongo_uri=settings.cosmos_mongo_uri,
        db_name=settings.cosmos_db_name,
        collection_name=settings.cosmos_collection_name,
        local_json_path=settings.local_db_json_path,
    )

    model = get_default_model(settings.model_path)
    return AppState(blob=blob, store=store, model=model)

