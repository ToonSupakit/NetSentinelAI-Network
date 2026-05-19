"""Model metadata and evaluation report helpers."""

from __future__ import annotations

import json
import os
from datetime import datetime


def metadata_path(model_path: str) -> str:
    root, ext = os.path.splitext(model_path)
    if ext:
        return f"{root}.meta.json"
    return f"{model_path}.meta.json"


def load_metadata(model_path: str) -> dict:
    path = metadata_path(model_path)
    if not os.path.exists(path):
        return {
            "configured_model_path": model_path,
            "metadata_path": path,
            "model_exists": os.path.exists(model_path),
            "trained": False,
        }
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        return {
            "configured_model_path": model_path,
            "metadata_path": path,
            "model_exists": os.path.exists(model_path),
            "trained": False,
            "metadata_error": str(exc),
        }
    data["configured_model_path"] = model_path
    data["metadata_path"] = path
    data["model_exists"] = os.path.exists(model_path)
    return data


def write_metadata(model_path: str, metadata: dict) -> str:
    path = metadata_path(model_path)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    payload = dict(metadata)
    payload.setdefault("model_path", model_path)
    payload.setdefault("written_at", datetime.now().isoformat(timespec="seconds"))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    return path
