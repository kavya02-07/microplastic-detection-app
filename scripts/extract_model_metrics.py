"""
Deterministic extraction of embedded research metrics from the deployed
YOLOv8 checkpoint (weights/t29.pt) into backend/core/model_metrics.json.

This is a READ-ONLY extraction:
  * The .pt weights file is opened with torch.load and never written back.
  * Only metadata already embedded in the checkpoint is copied out — nothing
    is computed, estimated, or inferred.

The resulting JSON is the single source of truth used by the API endpoint and
the PDF report, so neither of those has to reload the 52 MB checkpoint at
runtime.

Run from the project root:
    .venv/Scripts/python.exe scripts/extract_model_metrics.py
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import torch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHECKPOINT_PATH = PROJECT_ROOT / "weights" / "t29.pt"
OUTPUT_PATH = PROJECT_ROOT / "backend" / "core" / "model_metrics.json"

# train_args keys that are relevant to a research/evaluation write-up.
RELEVANT_TRAIN_ARGS = ["task", "mode", "model", "data", "epochs", "imgsz",
                       "batch", "optimizer", "seed", "lr0", "lrf"]

# The four aggregate validation metrics we surface as headline figures, mapped
# to friendly labels. "(B)" is Ultralytics' box-detection metric family.
FINAL_METRIC_KEYS = {
    "metrics/precision(B)": "precision",
    "metrics/recall(B)": "recall",
    "metrics/mAP50(B)": "map50",
    "metrics/mAP50-95(B)": "map50_95",
}

# Per-epoch series copied verbatim from train_results.
HISTORY_KEYS = [
    "epoch",
    "train/box_loss", "train/cls_loss", "train/dfl_loss",
    "val/box_loss", "val/cls_loss", "val/dfl_loss",
    "metrics/precision(B)", "metrics/recall(B)",
    "metrics/mAP50(B)", "metrics/mAP50-95(B)",
    "lr/pg0", "lr/pg1", "lr/pg2",
]


def _to_plain(value):
    """Convert torch tensors / numpy scalars to JSON-safe Python floats."""
    if value is None:
        return None
    if hasattr(value, "item"):  # torch tensor or numpy scalar
        try:
            return value.item()
        except Exception:
            pass
    if isinstance(value, (list, tuple)):
        return [_to_plain(v) for v in value]
    return value


def extract(checkpoint_path: Path = CHECKPOINT_PATH) -> dict:
    """Load the checkpoint and return a JSON-safe metrics dict. Never writes."""
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

    # weights_only=False is required to read the training metadata dict that
    # Ultralytics stores alongside the model.
    ckpt = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    if not isinstance(ckpt, dict):
        raise ValueError("Checkpoint is not a metadata dict; cannot extract.")

    train_args = ckpt.get("train_args") or {}
    if hasattr(train_args, "__dict__") and not isinstance(train_args, dict):
        train_args = vars(train_args)

    model = ckpt.get("model")
    names = None
    if model is not None:
        names = getattr(model, "names", None)
    if names is not None:
        # Ensure integer keys serialize cleanly and in order.
        names = {int(k): str(v) for k, v in dict(names).items()}

    train_metrics = ckpt.get("train_metrics") or {}
    final_validation = {}
    for src_key, out_key in FINAL_METRIC_KEYS.items():
        if src_key in train_metrics:
            final_validation[out_key] = _to_plain(train_metrics[src_key])

    # Full per-epoch history (verbatim copy of the recorded series).
    tr = ckpt.get("train_results") or {}
    history = {}
    for key in HISTORY_KEYS:
        if key in tr:
            history[key] = [_to_plain(v) for v in tr[key]]
    epoch_count = len(history.get("epoch", []))

    training_config = {
        "task": train_args.get("task"),
        "base_model": train_args.get("model"),
        "epochs": train_args.get("epochs"),
        "imgsz": train_args.get("imgsz"),
        "batch": train_args.get("batch"),
        "optimizer": train_args.get("optimizer"),
        "seed": train_args.get("seed"),
        "lr0": train_args.get("lr0"),
        "lrf": train_args.get("lrf"),
        # The original training data path is external (a Colab mount) and is
        # preserved ONLY as historical metadata — the dataset is not in this repo.
        "training_data_source": train_args.get("data"),
        "run_name": train_args.get("name"),
    }

    result = {
        "evidence_type": "training_run_validation",
        "extracted_at": datetime.now(timezone.utc).isoformat(),
        "source_checkpoint": checkpoint_path.name,
        "model": {
            "architecture": "YOLOv8 Medium",
            "deployed_checkpoint": checkpoint_path.name,
            "framework": "Ultralytics",
            "ultralytics_version": ckpt.get("version"),
            "checkpoint_date": ckpt.get("date"),
            "license": ckpt.get("license"),
            "num_classes": len(names) if names else None,
            "class_names": names,
        },
        "training_config": training_config,
        "final_validation_metrics": final_validation,
        "epoch_history": history,
        "epoch_count": epoch_count,
        "notes": {
            "evidence_type": "training_run_validation",
            "dataset_in_repo": False,
            "independent_test_set": False,
            "per_class_ground_truth": False,
            "description": (
                "Metrics are validation-split figures recorded during the "
                "original training run and embedded in the deployed checkpoint. "
                "The training dataset is not included in this repository, so "
                "they cannot be independently reproduced here. No independent "
                "held-out test set or per-class ground truth is available."
            ),
        },
    }
    return result


def main() -> int:
    print(f"Reading checkpoint: {CHECKPOINT_PATH}")
    data = extract()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    fv = data["final_validation_metrics"]
    print(f"Wrote: {OUTPUT_PATH}")
    print(f"  evidence_type       : {data['evidence_type']}")
    print(f"  checkpoint date     : {data['model']['checkpoint_date']}")
    print(f"  classes             : {data['model']['class_names']}")
    print(f"  epochs in history   : {data['epoch_count']}")
    print(f"  final precision     : {fv.get('precision')}")
    print(f"  final recall        : {fv.get('recall')}")
    print(f"  final mAP50         : {fv.get('map50')}")
    print(f"  final mAP50-95      : {fv.get('map50_95')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
