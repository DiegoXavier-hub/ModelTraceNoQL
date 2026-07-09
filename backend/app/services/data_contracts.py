from __future__ import annotations

from typing import Any

from app.core.utils import get_nested


def _value_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "numeric"
    if isinstance(value, str):
        return "text"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    if value is None:
        return "null"
    return type(value).__name__


def _matches_type(value: Any, expected: str | None) -> bool:
    if value is None or not expected:
        return True
    if expected == "numeric":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected in {"categorical", "text", "datetime"}:
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    return True


def validate_prediction_contract(project: dict, model: dict, features: dict[str, Any]) -> dict[str, Any]:
    mode = get_nested(project, "settings.data_contract_mode", "warn")
    expected = model.get("expected_features") or []
    issues: list[dict[str, Any]] = []

    for feature in expected:
        name = feature.get("name")
        if not name:
            continue
        value = features.get(name)
        required = bool(feature.get("required", False))
        nullable = bool(feature.get("nullable", False))
        if required and value in (None, "") and not nullable:
            issues.append({"feature": name, "code": "missing_required", "severity": "high", "message": "Feature obrigatoria ausente."})
            continue
        if value in (None, ""):
            continue
        expected_type = feature.get("type")
        if not _matches_type(value, expected_type):
            issues.append(
                {
                    "feature": name,
                    "code": "type_mismatch",
                    "severity": "high",
                    "message": f"Tipo esperado {expected_type}; recebido {_value_type(value)}.",
                    "expected_type": expected_type,
                    "observed_type": _value_type(value),
                }
            )
            continue
        if expected_type == "numeric":
            numeric = float(value)
            if feature.get("min") is not None and numeric < float(feature["min"]):
                issues.append({"feature": name, "code": "below_min", "severity": "medium", "message": f"Valor abaixo do minimo {feature['min']}."})
            if feature.get("max") is not None and numeric > float(feature["max"]):
                issues.append({"feature": name, "code": "above_max", "severity": "medium", "message": f"Valor acima do maximo {feature['max']}."})
        allowed = feature.get("allowed_values")
        if allowed and str(value) not in {str(item) for item in allowed}:
            issues.append({"feature": name, "code": "unexpected_value", "severity": "medium", "message": "Valor fora da lista permitida."})

    expected_names = {feature.get("name") for feature in expected if feature.get("name")}
    extra_features = sorted(set(features) - expected_names) if expected_names else []
    for name in extra_features[:20]:
        issues.append({"feature": name, "code": "unexpected_feature", "severity": "low", "message": "Feature nao declarada no contrato."})

    blocking = mode == "block" and any(issue["severity"] in {"high", "critical"} for issue in issues)
    return {
        "mode": mode,
        "status": "fail" if blocking else "warn" if issues else "pass",
        "blocking": blocking,
        "issues": issues,
        "issue_count": len(issues),
    }
