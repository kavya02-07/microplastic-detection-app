"""
MicroplasticDetector — reusable inference wrapper around YOLO.

This is the single entry point for running microplastic detection.
The model is loaded ONCE at initialization and reused for every
subsequent detect() call. The weights file is never modified.

Usage:
    from backend.core.detector import MicroplasticDetector

    detector = MicroplasticDetector("weights/t29.pt")
    result = detector.detect("path/to/image.png", confidence=0.4)
    print(result.summary.total_detections)
    print(result.to_dict())
"""

import time
from pathlib import Path
from typing import Union

import numpy as np
from PIL import Image
from ultralytics import YOLO

from backend.core.postprocessor import build_detected_objects, build_summary
from backend.core.schemas import DetectionResult


class MicroplasticDetector:
    """
    Wraps the YOLO model for microplastic detection.

    The model file (weights/t29.pt) is loaded once into memory
    and reused across all calls to detect(). This avoids the
    costly reload that the existing Streamlit app does on every
    page interaction.

    The detector accepts three input types:
      - file path (str or Path)
      - PIL Image
      - numpy ndarray (H×W×C, BGR or RGB)

    It returns a DetectionResult containing structured per-object
    data and sample-level summary statistics.
    """

    def __init__(self, model_path: str = "weights/t29.pt") -> None:
        """
        Load the YOLO model from disk.

        Args:
            model_path: Path to the .pt weights file.

        Raises:
            FileNotFoundError: If the weights file does not exist.
        """
        self._model_path = Path(model_path)

        if not self._model_path.exists():
            raise FileNotFoundError(
                f"Model weights not found: {self._model_path.resolve()}"
            )

        self._model = YOLO(str(self._model_path))
        self._model_name = self._model_path.stem  # e.g. "t29"

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------

    @property
    def model_name(self) -> str:
        """Name of the loaded model (stem of the weights filename)."""
        return self._model_name

    @property
    def model_class_names(self) -> dict:
        """Raw class name mapping as stored inside the model."""
        return self._model.names

    # ------------------------------------------------------------------
    # Core detection method
    # ------------------------------------------------------------------

    def detect(
        self,
        image: Union[str, Path, Image.Image, np.ndarray],
        confidence: float = 0.4,
    ) -> DetectionResult:
        """
        Run microplastic detection on a single image.

        Args:
            image: The input image. Accepts:
                   - str or Path: file path to an image
                   - PIL.Image.Image: an already-opened image
                   - numpy.ndarray: array in shape (H, W, C)
            confidence: Minimum confidence threshold, 0.0–1.0.
                        Detections below this score are discarded
                        by YOLO before results are returned.

        Returns:
            DetectionResult containing:
              - objects: list of DetectedObject (one per particle)
              - summary: DetectionSummary with counts, avg conf, timing
              - image dimensions and metadata

        Raises:
            ValueError: If confidence is outside [0.0, 1.0].
            TypeError: If the image type is not supported.
            FileNotFoundError: If a path-type image does not exist.
        """
        # --- Validate inputs ---
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(
                f"Confidence must be between 0.0 and 1.0, got {confidence}"
            )

        # --- Resolve image and extract dimensions ---
        if isinstance(image, (str, Path)):
            image_path = Path(image)
            if not image_path.exists():
                raise FileNotFoundError(f"Image not found: {image_path}")
            image = Image.open(image_path)

        if isinstance(image, Image.Image):
            img_width, img_height = image.size
        elif isinstance(image, np.ndarray):
            img_height, img_width = image.shape[:2]
        else:
            raise TypeError(
                f"Unsupported image type: {type(image).__name__}. "
                "Expected str, Path, PIL.Image, or numpy.ndarray."
            )

        # --- Run YOLO inference with timing ---
        start = time.perf_counter()
        results = self._model.predict(image, conf=confidence, verbose=False)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        # --- Post-process into structured result ---
        yolo_result = results[0]
        objects = build_detected_objects(yolo_result)
        summary = build_summary(objects, elapsed_ms)

        return DetectionResult(
            objects=objects,
            summary=summary,
            image_width=img_width,
            image_height=img_height,
            confidence_threshold=confidence,
            model_name=self._model_name,
        )
