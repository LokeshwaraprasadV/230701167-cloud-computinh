from __future__ import annotations

from typing import Literal, TypedDict


DrStage = Literal["No DR", "Mild", "Moderate", "Severe", "Proliferative"]


class PatientData(TypedDict):
    name: str
    age: int
    gender: str
    diabetes_duration: float
    sugar_level: float

