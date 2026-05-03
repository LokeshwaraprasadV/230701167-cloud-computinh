from __future__ import annotations

from fastapi import APIRouter, Request


router = APIRouter()


@router.get("/azure/check")
def azure_check(request: Request):
    """
    Returns whether Azure services are configured and reachable.
    Safe for beginners: no secrets returned.
    """
    services = request.app.state.services

    blob_ok = False
    blob_mode = services.blob.__class__.__name__
    blob_error = None
    try:
        services.blob.ensure_container()
        blob_ok = True
    except Exception as e:
        blob_ok = False
        blob_error = str(e)

    db_ok = False
    db_mode = services.store.__class__.__name__
    db_error = None
    try:
        # Lightweight ping that works for Mongo driver
        if hasattr(services.store, "client"):
            services.store.client.admin.command("ping")
        else:
            # Local JSON fallback
            pass
        db_ok = True
    except Exception as e:
        db_ok = False
        db_error = str(e)

    return {
        "blob": {"ok": blob_ok, "mode": blob_mode, "error": blob_error},
        "db": {"ok": db_ok, "mode": db_mode, "error": db_error},
    }


@router.get("/azure/blob/recent")
def azure_blob_recent(request: Request, prefix: str = "images", limit: int = 25):
    """
    Lists blobs to confirm uploads landed in the expected container/prefix.
    """
    services = request.app.state.services
    try:
        items = services.blob.recent_blobs(prefix=prefix, limit=limit)
        return {"ok": True, "mode": services.blob.__class__.__name__, "prefix": prefix, "items": items}
    except Exception as e:
        return {"ok": False, "mode": services.blob.__class__.__name__, "prefix": prefix, "error": str(e), "items": []}

