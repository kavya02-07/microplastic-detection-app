"""
Structured data models for detection results.

Uses Python stdlib dataclasses only — no external dependencies required.
These are the return types for MicroplasticDetector.detect().
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class BoundingBox:
    """
    Bounding box in xyxy format (absolute pixel coordinates).

    Attributes:
        x1: Left edge x-coordinate.
        y1: Top edge y-coordinate.
        x2: Right edge x-coordinate.
        y2: Bottom edge y-coordinate.
    """

    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        """Width of the bounding box in pixels."""
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        """Height of the bounding box in pixels."""
        return self.y2 - self.y1

    @property
    def area(self) -> float:
        """Area of the bounding box in square pixels."""
        return self.width * self.height

    @property
    def aspect_ratio(self) -> float:
        """Width / height ratio. Returns 0.0 if height is zero."""
        if self.height == 0:
            return 0.0
        return self.width / self.height


@dataclass(frozen=True)
class DetectedObject:
    """
    A single detected microplastic particle.

    Attributes:
        class_id: Integer class ID from the YOLO model (0-3).
        class_name: Human-readable display name (e.g. "Fibers").
        confidence: Detection confidence score (0.0 to 1.0).
        bbox: Bounding box in xyxy pixel coordinates.
    """

    class_id: int
    class_name: str
    confidence: float
    bbox: BoundingBox

    @property
    def width(self) -> float:
        """Width of the bounding box in pixels."""
        return self.bbox.width

    @property
    def height(self) -> float:
        """Height of the bounding box in pixels."""
        return self.bbox.height

    @property
    def area(self) -> float:
        """Area of the bounding box in square pixels."""
        return self.bbox.area

    @property
    def aspect_ratio(self) -> float:
        """Width / height aspect ratio of the bounding box."""
        return self.bbox.aspect_ratio

    def to_dict(self) -> dict:
        """Serialize to a plain dictionary (JSON-safe)."""
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": round(self.confidence, 4),
            "bbox": {
                "x1": round(self.bbox.x1, 2),
                "y1": round(self.bbox.y1, 2),
                "x2": round(self.bbox.x2, 2),
                "y2": round(self.bbox.y2, 2),
            },
            "width": round(self.width, 2),
            "height": round(self.height, 2),
            "area": round(self.area, 2),
            "aspect_ratio": round(self.aspect_ratio, 4),
        }


@dataclass(frozen=True)
class DetectionSummary:
    """
    Sample-level summary statistics for one detection run.

    Attributes:
        total_detections: Total number of objects detected.
        counts_by_class: Mapping of display class name → count.
        average_confidence: Mean confidence across all detections.
        inference_time_ms: Model inference time in milliseconds.
    """

    total_detections: int
    counts_by_class: Dict[str, int]
    average_confidence: float
    inference_time_ms: float

    def to_dict(self) -> dict:
        """Serialize to a plain dictionary (JSON-safe)."""
        return {
            "total_detections": self.total_detections,
            "counts_by_class": dict(self.counts_by_class),
            "average_confidence": round(self.average_confidence, 4),
            "inference_time_ms": round(self.inference_time_ms, 2),
        }


@dataclass(frozen=True)
class DetectionResult:
    """
    Complete detection result for a single image.

    This is the top-level return type from MicroplasticDetector.detect().

    Attributes:
        objects: List of every detected microplastic particle.
        summary: Aggregated statistics for the entire image.
        image_width: Width of the input image in pixels.
        image_height: Height of the input image in pixels.
        confidence_threshold: Confidence threshold used for this run.
        model_name: Name of the model that produced these results.
    """

    objects: List[DetectedObject]
    summary: DetectionSummary
    image_width: int
    image_height: int
    confidence_threshold: float
    model_name: str

    def to_dict(self) -> dict:
        """Serialize the full result to a plain dictionary (JSON-safe)."""
        return {
            "objects": [obj.to_dict() for obj in self.objects],
            "summary": self.summary.to_dict(),
            "image_width": self.image_width,
            "image_height": self.image_height,
            "confidence_threshold": self.confidence_threshold,
            "model_name": self.model_name,
        }
