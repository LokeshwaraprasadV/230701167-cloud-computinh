from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Optional

import numpy as np

from app.core.types import DrStage, PatientData


DR_CLASSES: list[DrStage] = ["No DR", "Mild", "Moderate", "Severe", "Proliferative"]


@dataclass
class PredictionResult:
    predicted_class: DrStage
    confidence: float
    probabilities: dict[DrStage, float]
    model_mode: str  # "trained_model" | "fallback_demo"


class DrModelService:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self._model: Optional[object] = None
        self._mode: str = "fallback_demo"
        self._tf = None

    def _try_load_model(self) -> None:
        if self._model is not None:
            return
        if not self.model_path or not os.path.exists(self.model_path):
            self._model = None
            self._mode = "fallback_demo"
            return

        try:
            import tensorflow as tf  # lazy import (optional dependency)

            self._tf = tf
            self._model = tf.keras.models.load_model(self.model_path)
            self._mode = "trained_model"
        except Exception:
            # If TensorFlow isn't installed / compatible, fall back to demo mode.
            self._tf = None
            self._model = None
            self._mode = "fallback_demo"

    def predict(self, image_tensor: np.ndarray, patient: PatientData) -> PredictionResult:
        """
        If a trained Keras model exists at MODEL_PATH, use it.
        Otherwise return a deterministic demo prediction so the app is fully runnable.
        """
        self._try_load_model()

        if self._model is not None:
            tf = self._tf
            logits = self._model(image_tensor, training=False)
            probs = tf.nn.softmax(logits, axis=-1).numpy()[0].astype(float)
        else:
            probs = self._demo_probabilities(image_tensor=image_tensor, patient=patient)

        probs = np.clip(probs, 1e-9, 1.0)
        probs = (probs / probs.sum()).astype(float)

        best_idx = int(np.argmax(probs))
        best_class = DR_CLASSES[best_idx]
        confidence = float(probs[best_idx] * 100.0)
        prob_map = {DR_CLASSES[i]: float(probs[i] * 100.0) for i in range(len(DR_CLASSES))}

        return PredictionResult(
            predicted_class=best_class,
            confidence=confidence,
            probabilities=prob_map,
            model_mode=self._mode,
        )

    def _demo_probabilities(self, image_tensor: np.ndarray, patient: PatientData) -> np.ndarray:
        """
        Beginner-friendly fallback: produce stable probabilities using image + patient data hash.
        Not medically meaningful; meant only to keep the full app runnable.
        """
        age = float(patient.get("age", 0))
        duration = float(patient.get("diabetes_duration", 0.0))
        sugar = float(patient.get("sugar_level", 0.0))

        img_mean = float(np.mean(image_tensor))
        base_risk = 0.15 + 0.01 * min(age, 80.0) + 0.03 * min(duration, 25.0) + 0.002 * min(sugar, 400.0)
        base_risk += 0.25 * abs(img_mean)  # tiny image influence
        base_risk = float(np.clip(base_risk, 0.0, 1.0))

        seed_text = f"{age}-{duration}-{sugar}-{img_mean}"
        seed = int(hashlib.sha256(seed_text.encode("utf-8")).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)

        # Create a smooth distribution that shifts to higher stages as risk increases.
        centers = np.array([0.05, 0.25, 0.5, 0.7, 0.88], dtype=np.float32)
        widths = np.array([0.12, 0.13, 0.14, 0.12, 0.1], dtype=np.float32)
        scores = np.exp(-((base_risk - centers) ** 2) / (2.0 * (widths**2)))

        noise = rng.normal(loc=1.0, scale=0.06, size=scores.shape).astype(np.float32)
        scores = np.clip(scores * noise, 1e-6, None)
        return (scores / np.sum(scores)).astype(np.float32)


def get_default_model(model_path: str) -> DrModelService:
    return DrModelService(model_path=model_path)

