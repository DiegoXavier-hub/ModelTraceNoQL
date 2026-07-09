from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or uuid.uuid4().hex[:8]


def get_nested(document: dict[str, Any], dotted_path: str, default: Any = None) -> Any:
    current: Any = document
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def set_nested(document: dict[str, Any], dotted_path: str, value: Any) -> None:
    current = document
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value


def compute_score_band(score: float) -> str:
    if score < 0.30:
        return "very_low"
    if score < 0.50:
        return "low"
    if score < 0.70:
        return "medium"
    if score < 0.85:
        return "high"
    return "very_high"


def compute_classification_result(predicted_positive: bool, actual_positive: bool) -> str:
    if predicted_positive and actual_positive:
        return "tp"
    if predicted_positive and not actual_positive:
        return "fp"
    if not predicted_positive and actual_positive:
        return "fn"
    return "tn"

