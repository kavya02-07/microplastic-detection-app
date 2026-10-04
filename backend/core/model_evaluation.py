"""
Read-only accessor for the extracted model evaluation metrics.

Loads backend/core/model_metrics.json ONCE and caches it in memory. This is
the single source of truth for the /model/evaluation endpoint and the PDF
report — neither ever reloads the 52 MB checkpoint at runtime.

The JSON is produced by scripts/extract_model_metrics.py.
"""

import json
from functools import lru_cache
from pathlib import Path

METRICS_PATH = Path(__file__).resolve().parent / "model_metrics.json"


@lru_cache(maxsize=1)
def get_model_evaluation() -> dict:
    """
    Return the cached model evaluation metrics dict.

    Raises FileNotFoundError if the extraction has not been run. The result is
    cached for the process lifetime; call get_model_evaluation.cache_clear()
    to force a re-read (not needed in normal operation).
    """
    if not METRICS_PATH.exists():
        raise FileNotFoundError(
            f"Model metrics file not found: {METRICS_PATH}. "
            "Run scripts/extract_model_metrics.py to generate it."
        )
    with open(METRICS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def is_available() -> bool:
    """True if the extracted metrics file exists on disk."""
    return METRICS_PATH.exists()
