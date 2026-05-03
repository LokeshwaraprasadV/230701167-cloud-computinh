from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.types import PatientData
from app.reports.pdf_report import generate_pdf_report
from app.services.image_preprocess import load_image_rgb, to_efficientnet_tensor

router = APIRouter()


@router.post("/predict")
async def predict(
    request: Request,
    image: UploadFile = File(...),
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    diabetes_duration: float = Form(...),
    sugar_level: float = Form(...),
):
    request_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    patient: PatientData = {
        "name": name,
        "age": int(age),
        "gender": gender,
        "diabetes_duration": float(diabetes_duration),
        "sugar_level": float(sugar_level),
    }

    image_bytes = await image.read()
    pil_img = load_image_rgb(image_bytes)
    tensor = to_efficientnet_tensor(pil_img, size=224)

    services = request.app.state.services
    pred = services.model.predict(tensor, patient)

    blob = services.blob
    img_ext = os.path.splitext(image.filename or "")[1].lower() or ".jpg"
    img_filename = f"{request_id}{img_ext}"

    upload_res = blob.upload_bytes(
        content=image_bytes,
        content_type=image.content_type or "image/jpeg",
        # Container is already named "images" in Azure.
        # Use a different prefix to avoid "images/images/..." confusion in the portal.
        prefix="retina",
        filename=img_filename,
    )

    # Save a local copy path if we can (for PDF embedding). If image was stored on Azure,
    # we still keep a local file to build the PDF.
    os.makedirs(settings.local_storage_dir, exist_ok=True)
    local_image_path = os.path.join(settings.local_storage_dir, "images", img_filename)
    os.makedirs(os.path.dirname(local_image_path), exist_ok=True)
    try:
        with open(local_image_path, "wb") as f:
            f.write(image_bytes)
    except Exception:
        local_image_path = None

    report = generate_pdf_report(
        out_dir=settings.reports_dir,
        report_id=request_id,
        patient=patient,
        prediction=pred.predicted_class,
        confidence=pred.confidence,
        image_path_on_disk=local_image_path,
    )

    store = services.store

    doc = {
        "request_id": request_id,
        "created_at": created_at,
        "patient": patient,
        "image": {
            "filename": image.filename,
            "content_type": image.content_type,
            "stored_blob_name": upload_res.blob_name,
            "url": upload_res.url,
        },
        "prediction": {
            "class": pred.predicted_class,
            "confidence": pred.confidence,
            "probabilities": pred.probabilities,
            "model_mode": pred.model_mode,
        },
        "report": {
            "filename": report.filename,
            "local_path": report.pdf_path,
        },
    }
    stored = store.insert_prediction(doc)

    return JSONResponse(
        {
            "request_id": request_id,
            "stored_id": stored.id,
            "created_at": created_at,
            "patient": patient,
            "image_url": upload_res.url,
            "image_blob_name": upload_res.blob_name,
            "prediction": {
                "label": pred.predicted_class,
                "confidence_percent": round(pred.confidence, 2),
                "probabilities_percent": {k: round(v, 2) for k, v in pred.probabilities.items()},
                "model_mode": pred.model_mode,
            },
            "report_url": f"/reports/{report.filename}",
        }
    )

