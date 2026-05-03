from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.state import build_app_state
from app.routes.azure_check import router as azure_router
from app.routes.predict import router as predict_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin, "*"] if settings.environment == "local" else [settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    os.makedirs(settings.reports_dir, exist_ok=True)
    app.mount("/reports", StaticFiles(directory=settings.reports_dir), name="reports")

    app.state.services = build_app_state(settings=settings)
    try:
        app.state.services.blob.ensure_container()
    except Exception:
        pass

    app.include_router(azure_router)
    app.include_router(predict_router)

    @app.get("/health")
    def health():
        return {"status": "ok", "app": settings.app_name, "env": settings.environment}

    return app


app = create_app()

