"""
Class mapping configuration for microplastic detection.

The YOLO model (weights/t29.pt) stores internal class names:
    {0: 'fiber', 1: 'film', 2: 'fragment', 3: 'pallet'}

This module provides the canonical display names used throughout
the new application WITHOUT modifying the trained model.

The model's internal names are never changed. This mapping is
applied only at the presentation layer.
"""

# Display names: human-readable, plural, corrected spelling
DISPLAY_NAMES: dict[int, str] = {
    0: "Fibers",
    1: "Films",
    2: "Fragments",
    3: "Pellets",
}


def get_display_name(class_id: int) -> str:
    """
    Get the display name for a model class ID.

    Args:
        class_id: Integer class ID from the YOLO model (0-3).

    Returns:
        Human-readable display name, or "Unknown (id)" for unmapped IDs.
    """
    return DISPLAY_NAMES.get(class_id, f"Unknown ({class_id})")


def get_all_class_ids() -> list[int]:
    """Return all known class IDs in order."""
    return sorted(DISPLAY_NAMES.keys())


def get_class_count() -> int:
    """Return the total number of known classes."""
    return len(DISPLAY_NAMES)
