from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from app.core.types import DrStage, PatientData


@dataclass
class ReportResult:
    pdf_path: str
    filename: str


def _stage_suggestions(stage: DrStage) -> list[str]:
    if stage == "No DR":
        return [
            "Maintain regular eye screening (at least yearly).",
            "Keep blood sugar within target range.",
            "Healthy diet, exercise, and follow your doctor’s plan.",
        ]
    if stage == "Mild":
        return [
            "Book an eye specialist visit for baseline assessment.",
            "Improve glycemic control and monitor blood pressure.",
            "Schedule follow-up screening as advised (often 6–12 months).",
        ]
    if stage == "Moderate":
        return [
            "See an ophthalmologist soon for detailed evaluation.",
            "Tighten blood sugar control; check blood pressure and lipids.",
            "Follow-up is usually more frequent (e.g., 3–6 months).",
        ]
    if stage == "Severe":
        return [
            "Urgent ophthalmology review is recommended.",
            "Discuss possible treatments and frequent monitoring.",
            "Control sugar, blood pressure, and cholesterol aggressively.",
        ]
    return [
        "Immediate specialist care is recommended.",
        "Treatment may be required (laser / injections / surgery depending on findings).",
        "Do not delay follow-up; vision risk is high.",
    ]


def generate_pdf_report(
    *,
    out_dir: str,
    report_id: str,
    patient: PatientData,
    prediction: DrStage,
    confidence: float,
    image_path_on_disk: Optional[str] = None,
) -> ReportResult:
    os.makedirs(out_dir, exist_ok=True)
    filename = f"report_{report_id}.pdf"
    pdf_path = os.path.join(out_dir, filename)

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, height - 2.2 * cm, "Diabetic Retinopathy Screening Report")

    c.setFont("Helvetica", 10)
    c.drawString(2 * cm, height - 3.0 * cm, "Disclaimer: This is an AI-assisted result and not a medical diagnosis.")

    y = height - 4.2 * cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Patient Details")
    y -= 0.7 * cm

    c.setFont("Helvetica", 11)
    rows = [
        ("Name", str(patient.get("name", ""))),
        ("Age", str(patient.get("age", ""))),
        ("Gender", str(patient.get("gender", ""))),
        ("Diabetes Duration (years)", str(patient.get("diabetes_duration", ""))),
        ("Sugar Level (mg/dL)", str(patient.get("sugar_level", ""))),
    ]
    for label, value in rows:
        c.drawString(2 * cm, y, f"{label}: {value}")
        y -= 0.55 * cm

    y -= 0.4 * cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Prediction")
    y -= 0.7 * cm
    c.setFont("Helvetica", 11)
    c.drawString(2 * cm, y, f"Stage: {prediction}")
    y -= 0.55 * cm
    c.drawString(2 * cm, y, f"Confidence: {confidence:.2f}%")
    y -= 0.8 * cm

    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Suggestions")
    y -= 0.7 * cm
    c.setFont("Helvetica", 11)
    for s in _stage_suggestions(prediction):
        c.drawString(2.4 * cm, y, f"- {s}")
        y -= 0.55 * cm

    if image_path_on_disk and os.path.exists(image_path_on_disk):
        try:
            y -= 0.4 * cm
            c.setFont("Helvetica-Bold", 12)
            c.drawString(2 * cm, y, "Retinal Image")
            y -= 0.6 * cm

            # Resize for PDF placement
            img = Image.open(image_path_on_disk).convert("RGB")
            max_w = width - 4 * cm
            max_h = 8.5 * cm
            img_w, img_h = img.size
            scale = min(max_w / img_w, max_h / img_h)
            draw_w = img_w * scale
            draw_h = img_h * scale
            img_tmp = os.path.join(out_dir, f"_tmp_{report_id}.jpg")
            img.resize((int(draw_w), int(draw_h))).save(img_tmp, "JPEG", quality=90)

            c.drawImage(img_tmp, 2 * cm, max(2 * cm, y - draw_h), width=draw_w, height=draw_h)
            try:
                os.remove(img_tmp)
            except Exception:
                pass
        except Exception:
            pass

    c.showPage()
    c.save()
    return ReportResult(pdf_path=pdf_path, filename=filename)

