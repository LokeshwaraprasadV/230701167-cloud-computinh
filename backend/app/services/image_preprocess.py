from __future__ import annotations

from io import BytesIO

import numpy as np
from PIL import Image


def load_image_rgb(image_bytes: bytes) -> Image.Image:
    img = Image.open(BytesIO(image_bytes))
    return img.convert("RGB")


def to_efficientnet_tensor(img: Image.Image, size: int = 224) -> np.ndarray:
    resized = img.resize((size, size))
    arr = np.array(resized, dtype=np.float32)
    # EfficientNet preprocess_input (TensorFlow) is basically: x = x / 127.5 - 1
    # We implement it here so the backend can run even when TensorFlow is not installed.
    arr = (arr / 127.5) - 1.0
    return np.expand_dims(arr, axis=0)

