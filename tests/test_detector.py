"""
Phase 1 integration test — MicroplasticDetector against weights/t29.pt.

Verifies that the new inference layer:
  1. Loads the existing model without errors
  2. Runs detection on a real sample image
  3. Returns correctly structured results
  4. Reports all four class names in the summary
  5. Produces reasonable numeric values

Run from the project root:
    .venv\\Scripts\\python.exe tests/test_detector.py
"""

import json
import sys
from pathlib import Path

# Ensure the project root is importable
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from backend.core.detector import MicroplasticDetector
from backend.core.class_map import DISPLAY_NAMES


SEPARATOR = "=" * 64


def test_model_loading():
    """Test 1: Model loads successfully."""
    print(f"\n{'[Test 1]':=<{len(SEPARATOR)}}")
    print("Loading model from weights/t29.pt ...")

    detector = MicroplasticDetector("weights/t29.pt")

    assert detector.model_name == "t29", \
        f"Expected model_name='t29', got '{detector.model_name}'"
    assert isinstance(detector.model_class_names, dict), \
        "model_class_names should be a dict"
    assert len(detector.model_class_names) == 4, \
        f"Expected 4 classes, got {len(detector.model_class_names)}"

    print(f"  Model name : {detector.model_name}")
    print(f"  Raw classes: {detector.model_class_names}")
    print("  PASSED")
    return detector


def test_detection(detector: MicroplasticDetector):
    """Test 2: Detection on sample image returns structured results."""
    print(f"\n{'[Test 2]':=<{len(SEPARATOR)}}")
    image_path = "images/example1.png"
    print(f"Running detection on {image_path} (confidence=0.40) ...")

    result = detector.detect(image_path, confidence=0.40)

    # Structural checks
    assert result.model_name == "t29"
    assert result.confidence_threshold == 0.40
    assert result.image_width > 0
    assert result.image_height > 0
    assert isinstance(result.objects, list)
    assert result.summary.total_detections == len(result.objects)
    assert result.summary.inference_time_ms > 0

    # Every class should appear in counts (even if zero)
    for display_name in DISPLAY_NAMES.values():
        assert display_name in result.summary.counts_by_class, \
            f"Missing class '{display_name}' in counts_by_class"

    # Each object should have valid fields
    for obj in result.objects:
        assert obj.class_id in DISPLAY_NAMES, \
            f"Unknown class_id {obj.class_id}"
        assert obj.class_name == DISPLAY_NAMES[obj.class_id]
        assert 0.0 < obj.confidence <= 1.0
        assert obj.width > 0
        assert obj.height > 0
        assert obj.area > 0
        assert obj.aspect_ratio > 0

    print(f"  Image size      : {result.image_width} x {result.image_height}")
    print(f"  Detections      : {result.summary.total_detections}")
    print(f"  Counts by class : {result.summary.counts_by_class}")
    print(f"  Avg confidence  : {result.summary.average_confidence:.4f}")
    print(f"  Inference time  : {result.summary.inference_time_ms:.2f} ms")
    print("  PASSED")
    return result


def test_per_object_detail(result):
    """Test 3: Print per-object details for manual inspection."""
    print(f"\n{'[Test 3]':=<{len(SEPARATOR)}}")
    print("Per-object breakdown:")

    for i, obj in enumerate(result.objects):
        print(
            f"  [{i:2d}] {obj.class_name:<10s} "
            f"conf={obj.confidence:.4f}  "
            f"bbox=({obj.bbox.x1:.1f}, {obj.bbox.y1:.1f}, "
            f"{obj.bbox.x2:.1f}, {obj.bbox.y2:.1f})  "
            f"size={obj.width:.1f}x{obj.height:.1f}  "
            f"area={obj.area:.1f}  "
            f"ar={obj.aspect_ratio:.3f}"
        )

    print("  PASSED")


def test_to_dict_serialization(result):
    """Test 4: to_dict() produces valid JSON-serializable output."""
    print(f"\n{'[Test 4]':=<{len(SEPARATOR)}}")
    print("Testing to_dict() JSON serialization ...")

    result_dict = result.to_dict()
    json_str = json.dumps(result_dict, indent=2)

    # Should be valid JSON
    parsed = json.loads(json_str)
    assert parsed["model_name"] == "t29"
    assert len(parsed["objects"]) == result.summary.total_detections

    # Print full structured output
    print(json_str)
    print("  PASSED")


def test_edge_cases(detector: MicroplasticDetector):
    """Test 5: Validate input guards."""
    print(f"\n{'[Test 5]':=<{len(SEPARATOR)}}")
    print("Testing input validation ...")

    # Bad confidence
    try:
        detector.detect("images/example1.png", confidence=1.5)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"  Confidence > 1.0 -> ValueError: {e}")

    try:
        detector.detect("images/example1.png", confidence=-0.1)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"  Confidence < 0.0 -> ValueError: {e}")

    # Bad image path
    try:
        detector.detect("nonexistent.png")
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError as e:
        print(f"  Missing file     -> FileNotFoundError: {e}")

    # Bad image type
    try:
        detector.detect(12345)
        assert False, "Should have raised TypeError"
    except TypeError as e:
        print(f"  Bad type (int)   -> TypeError: {e}")

    print("  PASSED")


def main():
    print(SEPARATOR)
    print("  Phase 1 Integration Test: MicroplasticDetector")
    print(SEPARATOR)

    detector = test_model_loading()
    result = test_detection(detector)
    test_per_object_detail(result)
    test_to_dict_serialization(result)
    test_edge_cases(detector)

    print(f"\n{SEPARATOR}")
    print("  ALL 5 TESTS PASSED")
    print(SEPARATOR)


if __name__ == "__main__":
    main()
