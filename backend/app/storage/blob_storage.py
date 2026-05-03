from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone

from azure.storage.blob import BlobServiceClient, ContentSettings


@dataclass
class BlobUploadResult:
    blob_name: str
    url: str


class BlobStorage:
    def __init__(self, connection_string: str, container_name: str, public_base_url: str = ""):
        self.connection_string = connection_string
        self.container_name = container_name
        self.public_base_url = public_base_url.strip()

        self._client = BlobServiceClient.from_connection_string(self.connection_string)
        self._container = self._client.get_container_client(self.container_name)

    def ensure_container(self) -> None:
        try:
            self._container.create_container()
        except Exception:
            return

    def upload_bytes(self, *, content: bytes, content_type: str, prefix: str, filename: str) -> BlobUploadResult:
        now = datetime.now(timezone.utc)
        safe_prefix = prefix.strip("/").replace("\\", "/")
        blob_name = f"{safe_prefix}/{now.strftime('%Y/%m/%d')}/{filename}"

        self._container.upload_blob(
            name=blob_name,
            data=content,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )

        if self.public_base_url:
            url = f"{self.public_base_url.rstrip('/')}/{self.container_name}/{blob_name}"
        else:
            url = self._container.get_blob_client(blob_name).url

        return BlobUploadResult(blob_name=blob_name, url=url)

    def recent_blobs(self, *, prefix: str = "", limit: int = 25) -> list[dict]:
        safe_prefix = (prefix or "").strip("/").replace("\\", "/")
        results: list[dict] = []
        # Include snapshots=False is default; using name_starts_with for "folder-like" prefixes.
        for b in self._container.list_blobs(name_starts_with=safe_prefix or None):
            results.append(
                {
                    "name": b.name,
                    "size": getattr(b, "size", None),
                    "last_modified": getattr(b, "last_modified", None).isoformat() if getattr(b, "last_modified", None) else None,
                }
            )
            if len(results) >= max(1, int(limit)):
                break
        return results


class LocalBlobFallback:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def ensure_container(self) -> None:
        return

    def upload_bytes(self, *, content: bytes, content_type: str, prefix: str, filename: str) -> BlobUploadResult:
        safe_prefix = prefix.strip("/").replace("\\", "/")
        out_dir = os.path.join(self.base_dir, safe_prefix)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, filename)
        with open(out_path, "wb") as f:
            f.write(content)
        return BlobUploadResult(blob_name=f"{safe_prefix}/{filename}", url=out_path)

    def recent_blobs(self, *, prefix: str = "", limit: int = 25) -> list[dict]:
        safe_prefix = (prefix or "").strip("/").replace("\\", "/")
        base = os.path.join(self.base_dir, safe_prefix) if safe_prefix else self.base_dir
        if not os.path.exists(base):
            return []
        out: list[dict] = []
        # Keep it simple (non-recursive) for the local fallback.
        for name in os.listdir(base):
            p = os.path.join(base, name)
            if os.path.isfile(p):
                out.append({"name": f"{safe_prefix}/{name}".strip("/"), "size": os.path.getsize(p), "last_modified": None})
            if len(out) >= max(1, int(limit)):
                break
        return out

