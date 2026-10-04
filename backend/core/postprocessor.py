"""
Post-processing logic for YOLO detection results.

Converts raw ultralytics Results objects into structured
DetectedObject lists and DetectionSummary statistics.

This module is internal to the inference layer — external code
should use MicroplasticDetector.detect() instead of calling
these functions directly.
"""

from typing import Dict, List

from backend.core.class_map import DISPLAY_NAMES, get_display_name
from backend.core.schemas import BoundingBox, DetectedObject, DetectionSummary


def build_detected_objects(yolo_result) -> List[DetectedObject]:
    """
    Extract a list of DetectedObject from a single YOLO result.

    Args:
        yolo_result: One element from ultralytics model.predict()
                     (i.e. results[0]).

    Returns:
        List of DetectedObject instances, one per detection.
        Empty list if nothing was detected.
    """
    objects: List[DetectedObject] = []
    boxes = yolo_result.boxes

    if boxes is None or len(boxes) == 0:
        return objects

    # Pull tensors to CPU as numpy arrays
    xyxy_arr = boxes.xyxy.cpu().numpy()
    conf_arr = boxes.conf.cpu().numpy()
    cls_arr = boxes.cls.cpu().numpy().astype(int)

    for i in range(len(boxes)):
        bbox = BoundingBox(
            x1=float(xyxy_arr[i][0]),
            y1=float(xyxy_arr[i][1]),
            x2=float(xyxy_arr[i][2]),
            y2=float(xyxy_arr[i][3]),
        )
        obj = DetectedObject(
            class_id=int(cls_arr[i]),
            class_name=get_display_name(int(cls_arr[i])),
            confidence=float(conf_arr[i]),
            bbox=bbox,
        )
        objects.append(obj)

    return objects


def build_summary(
    objects: List[DetectedObject],
    inference_time_ms: float,
) -> DetectionSummary:
    """
    Build sample-level summary statistics from detected objects.

    All four class names always appear in counts_by_class, even
    if their count is zero. This makes downstream processing
    (charts, tables) simpler.

    Args:
        objects: List of DetectedObject from build_detected_objects().
        inference_time_ms: Elapsed inference time in milliseconds.

    Returns:
        DetectionSummary with counts, average confidence, and timing.
    """
    total = len(objects)

    # Initialize all classes to zero so every class is always present
    counts: Dict[str, int] = {name: 0 for name in DISPLAY_NAMES.values()}
    for obj in objects:
        if obj.class_name in counts:
            counts[obj.class_name] += 1
        else:
            counts[obj.class_name] = 1

    avg_conf = 0.0
    if total > 0:
        avg_conf = sum(obj.confidence for obj in objects) / total

    return DetectionSummary(
        total_detections=total,
        counts_by_class=counts,
        average_confidence=avg_conf,
        inference_time_ms=inference_time_ms,
    )
