from __future__ import annotations

from typing import Any

from app.core.utils import get_nested


def _risk_factor(feature: str, value: Any) -> float | None:
    try:
        if feature == "attendance_rate":
            return 1 - float(value)
        if feature == "avg_grade":
            return 1 - (float(value) / 100)
        if feature == "failed_subjects":
            return min(float(value) / 5, 1)
        if feature == "credits_completed":
            return 1 - min(float(value) / 120, 1)
        if feature == "night_shift":
            return 1.0 if bool(value) else 0.0
        if feature == "scholarship":
            return 0.0 if bool(value) else 1.0
    except (TypeError, ValueError):
        return None
    return None


def estimate_what_if(prediction: dict[str, Any], hypothetical_features: dict[str, Any]) -> dict[str, Any]:
    original_features = prediction.get("features", {})
    base_score = float(get_nested(prediction, "prediction.score", 0))
    threshold = float(get_nested(prediction, "prediction.threshold", 0.5))
    impacts = {row.get("feature"): float(row.get("impact", 0)) for row in prediction.get("explanations", [])}
    changes = []
    estimated_score = base_score

    for feature, new_value in hypothetical_features.items():
        old_value = original_features.get(feature)
        if old_value == new_value:
            continue
        old_risk = _risk_factor(feature, old_value)
        new_risk = _risk_factor(feature, new_value)
        impact = impacts.get(feature, 0.02)
        if old_risk is not None and new_risk is not None:
            delta = impact * (new_risk - old_risk)
        else:
            delta = impact * 0.15
        estimated_score += delta
        changes.append(
            {
                "feature": feature,
                "from": old_value,
                "to": new_value,
                "estimated_delta": round(delta, 4),
            }
        )

    estimated_score = round(max(0.0, min(1.0, estimated_score)), 4)
    return {
        "prediction_id": prediction["_id"],
        "original_score": base_score,
        "estimated_score": estimated_score,
        "estimated_delta": round(estimated_score - base_score, 4),
        "threshold": threshold,
        "would_change_decision": (base_score >= threshold) != (estimated_score >= threshold),
        "changed_features": changes,
        "methodological_warning": "Estimativa baseada em impactos registrados; nao executa o modelo real.",
    }
