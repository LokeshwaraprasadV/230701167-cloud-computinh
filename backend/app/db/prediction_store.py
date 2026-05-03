from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional, Protocol
from json import JSONDecodeError

from pymongo import MongoClient


@dataclass
class StoredPrediction:
    id: str
    created_at: str


class PredictionStore(Protocol):
    def insert_prediction(self, doc: dict[str, Any]) -> StoredPrediction: ...


class CosmosMongoStore:
    def __init__(self, mongo_uri: str, db_name: str, collection_name: str):
        # Keep timeouts short so the app stays responsive even if Cosmos is blocked.
        self.client = MongoClient(mongo_uri, connectTimeoutMS=6000, socketTimeoutMS=6000, serverSelectionTimeoutMS=6000)
        self.collection = self.client[db_name][collection_name]

        try:
            self.collection.create_index("created_at")
        except Exception:
            pass

    def insert_prediction(self, doc: dict[str, Any]) -> StoredPrediction:
        if "created_at" not in doc:
            doc["created_at"] = datetime.now(timezone.utc).isoformat()
        res = self.collection.insert_one(doc)
        return StoredPrediction(id=str(res.inserted_id), created_at=str(doc["created_at"]))


class LocalJsonStore:
    def __init__(self, json_path: str):
        self.json_path = json_path
        os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
        if not os.path.exists(self.json_path):
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump({"predictions": []}, f, indent=2)

    def insert_prediction(self, doc: dict[str, Any]) -> StoredPrediction:
        created_at = doc.get("created_at") or datetime.now(timezone.utc).isoformat()
        doc["created_at"] = created_at

        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, JSONDecodeError):
            data = {"predictions": []}
        data.setdefault("predictions", []).append(doc)
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        pred_id = str(len(data["predictions"]) - 1)
        return StoredPrediction(id=pred_id, created_at=created_at)


class ResilientStore:
    """
    Try Cosmos first; if it fails, fall back to local JSON so /predict still works.
    This helps beginners verify Azure Blob uploads even before Cosmos networking is fixed.
    """

    def __init__(self, primary: PredictionStore, fallback: PredictionStore):
        self.primary = primary
        self.fallback = fallback

    def insert_prediction(self, doc: dict[str, Any]) -> StoredPrediction:
        try:
            return self.primary.insert_prediction(doc)
        except Exception:
            return self.fallback.insert_prediction(doc)


def build_prediction_store(
    *,
    cosmos_mongo_uri: str,
    db_name: str,
    collection_name: str,
    local_json_path: str,
):
    cosmos_mongo_uri = (cosmos_mongo_uri or "").strip()
    local = LocalJsonStore(local_json_path)
    if not cosmos_mongo_uri:
        return local

    try:
        cosmos = CosmosMongoStore(cosmos_mongo_uri, db_name, collection_name)
        return ResilientStore(primary=cosmos, fallback=local)
    except Exception:
        return local

