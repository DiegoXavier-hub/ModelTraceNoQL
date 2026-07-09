from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from app.core.privacy import reveal_entity
from app.core.utils import get_nested, utcnow
from app.db.document_store import DocumentStore


DIAGNOSTIC_CACHE_VERSION = 2
THRESHOLDS = [round(value / 100, 2) for value in range(5, 100, 5)]
SCORE_BINS = [
    (0.0, 0.1),
    (0.1, 0.2),
    (0.2, 0.3),
    (0.3, 0.4),
    (0.4, 0.5),
    (0.5, 0.6),
    (0.6, 0.7),
    (0.7, 0.8),
    (0.8, 0.9),
    (0.9, 1.01),
]


def _safe_div(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def _round(value: float | None, digits: int = 4) -> float | None:
    return round(value, digits) if value is not None else None


def _score(item: dict[str, Any]) -> float:
    return float(get_nested(item, "prediction.score", 0) or 0)


def _actual_positive(item: dict[str, Any]) -> bool | None:
    result = get_nested(item, "feedback.classification_result")
    if result in {"tp", "fn"}:
        return True
    if result in {"fp", "tn"}:
        return False
    observed = get_nested(item, "feedback.observed_value")
    if observed is not None:
        return bool(observed)
    return None


def _type_ok(value: Any, expected_type: str | None) -> bool:
    if value is None or expected_type is None:
        return True
    if expected_type == "numeric":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type in {"categorical", "text", "datetime"}:
        return isinstance(value, str)
    return True


def _threshold_metrics(scored_feedback: list[tuple[float, bool]], all_scores: list[float], threshold: float) -> dict[str, Any]:
    tp = fp = tn = fn = 0
    for score, actual in scored_feedback:
        predicted = score >= threshold
        if predicted and actual:
            tp += 1
        elif predicted and not actual:
            fp += 1
        elif not predicted and not actual:
            tn += 1
        else:
            fn += 1
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    accuracy = _safe_div(tp + tn, tp + fp + tn + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall) if precision and recall else None
    f2 = _safe_div(5 * precision * recall, (4 * precision) + recall) if precision and recall else None
    predicted_all = sum(1 for score in all_scores if score >= threshold)
    return {
        "threshold": threshold,
        "precision": _round(precision),
        "recall": _round(recall),
        "accuracy": _round(accuracy),
        "f1": _round(f1),
        "f2": _round(f2),
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "predicted_positive": predicted_all,
        "workload_rate": _round(_safe_div(predicted_all, len(all_scores)) or 0),
    }


def _calibration(scored_feedback: list[tuple[float, bool]]) -> dict[str, Any]:
    rows = []
    total = len(scored_feedback)
    weighted_gap = 0.0
    brier_values = []
    for start, end in SCORE_BINS:
        items = [(score, actual) for score, actual in scored_feedback if start <= score < end]
        if items:
            avg_score = mean(score for score, _ in items)
            observed_rate = mean(1 if actual else 0 for _, actual in items)
            gap = abs(avg_score - observed_rate)
            weighted_gap += (len(items) / total) * gap if total else 0
        else:
            avg_score = observed_rate = gap = None
        rows.append(
            {
                "bucket": f"{start:.1f}-{min(end, 1.0):.1f}",
                "count": len(items),
                "avg_score": _round(avg_score),
                "observed_rate": _round(observed_rate),
                "gap": _round(gap),
            }
        )
    for score, actual in scored_feedback:
        brier_values.append((score - (1 if actual else 0)) ** 2)
    return {
        "bins": rows,
        "ece": _round(weighted_gap),
        "brier_score": _round(mean(brier_values) if brier_values else None),
    }


def _feature_importance(predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {"count": 0, "abs_sum": 0.0, "sum": 0.0})
    for item in predictions:
        for explanation in item.get("explanations") or []:
            feature = explanation.get("feature")
            if not feature:
                continue
            try:
                impact = float(explanation.get("impact") or 0)
            except (TypeError, ValueError):
                continue
            grouped[feature]["count"] += 1
            grouped[feature]["abs_sum"] += abs(impact)
            grouped[feature]["sum"] += impact
    rows = []
    total = max(len(predictions), 1)
    for feature, values in grouped.items():
        count = values["count"]
        avg_impact = values["sum"] / count if count else 0
        rows.append(
            {
                "feature": feature,
                "count": count,
                "coverage": _round(count / total),
                "avg_abs_impact": _round(values["abs_sum"] / count if count else 0),
                "avg_impact": _round(avg_impact),
                "dominant_direction": "raises_score" if avg_impact >= 0 else "lowers_score",
            }
        )
    return sorted(rows, key=lambda row: row["avg_abs_impact"] or 0, reverse=True)[:20]


def _feature_coverage(model: dict[str, Any], predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expected = model.get("expected_features") or []
    total = max(len(predictions), 1)
    rows = []
    for feature in expected:
        name = feature.get("name")
        if not name:
            continue
        present = 0
        type_mismatch = 0
        examples = Counter()
        for item in predictions:
            features = item.get("features") or {}
            value = features.get(name)
            if value not in (None, ""):
                present += 1
                examples[str(value)[:40]] += 1
                if not _type_ok(value, feature.get("type")):
                    type_mismatch += 1
        rows.append(
            {
                "feature": name,
                "type": feature.get("type", "unknown"),
                "required": bool(feature.get("required", False)),
                "coverage": _round(present / total),
                "missing_rate": _round(1 - (present / total)),
                "type_mismatch": type_mismatch,
                "top_values": [{"value": value, "count": count} for value, count in examples.most_common(3)],
            }
        )
    return sorted(rows, key=lambda row: (row["required"] is False, -(row["missing_rate"] or 0)))[:30]


def _candidate_features(model: dict[str, Any], predictions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for feature in model.get("expected_features") or []:
        name = feature.get("name")
        if not name:
            continue
        values = [
            (item.get("features") or {}).get(name)
            for item in predictions
            if (item.get("features") or {}).get(name) not in (None, "")
        ]
        if not values:
            continue
        unique_count = len({str(value) for value in values[:2500]})
        candidates.append(
            {
                "feature": name,
                "type": feature.get("type", "unknown"),
                "coverage": _round(len(values) / max(len(predictions), 1)),
                "sample_unique": unique_count,
            }
        )
    return sorted(candidates, key=lambda item: (item["type"] == "numeric", -(item["coverage"] or 0), item["sample_unique"]))[:20]


def _group_key(value: Any, numeric_edges: list[float] | None = None) -> str:
    if value in (None, ""):
        return "missing"
    if numeric_edges and isinstance(value, (int, float)) and not isinstance(value, bool):
        if value <= numeric_edges[0]:
            return f"<= {numeric_edges[0]:.3g}"
        if value <= numeric_edges[1]:
            return f"{numeric_edges[0]:.3g} - {numeric_edges[1]:.3g}"
        if value <= numeric_edges[2]:
            return f"{numeric_edges[1]:.3g} - {numeric_edges[2]:.3g}"
        return f"> {numeric_edges[2]:.3g}"
    return str(value)[:60]


def _slice_rows(predictions: list[dict[str, Any]], feature: str, positive_label: str) -> list[dict[str, Any]]:
    numeric_values = [
        (item.get("features") or {}).get(feature)
        for item in predictions
        if isinstance((item.get("features") or {}).get(feature), (int, float))
        and not isinstance((item.get("features") or {}).get(feature), bool)
    ]
    numeric_edges = None
    if len(numeric_values) >= 20:
        ordered = sorted(float(value) for value in numeric_values)
        numeric_edges = [
            ordered[int((len(ordered) - 1) * 0.25)],
            ordered[int((len(ordered) - 1) * 0.50)],
            ordered[int((len(ordered) - 1) * 0.75)],
        ]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in predictions:
        grouped[_group_key((item.get("features") or {}).get(feature), numeric_edges)].append(item)

    rows = []
    for group, items in grouped.items():
        if not items:
            continue
        feedback = [item for item in items if _actual_positive(item) is not None]
        tp = sum(1 for item in feedback if get_nested(item, "feedback.classification_result") == "tp")
        fp = sum(1 for item in feedback if get_nested(item, "feedback.classification_result") == "fp")
        fn = sum(1 for item in feedback if get_nested(item, "feedback.classification_result") == "fn")
        positives = sum(1 for item in items if get_nested(item, "prediction.label") == positive_label)
        rows.append(
            {
                "group": group,
                "total": len(items),
                "avg_score": _round(mean(_score(item) for item in items)),
                "positive_rate": _round(positives / len(items)),
                "feedback": len(feedback),
                "precision": _round(_safe_div(tp, tp + fp)),
                "recall": _round(_safe_div(tp, tp + fn)),
            }
        )
    return sorted(rows, key=lambda row: row["total"], reverse=True)[:12]


def _error_examples(predictions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows = []
    for item in predictions:
        result = get_nested(item, "feedback.classification_result")
        if result not in {"fp", "fn"}:
            continue
        explanations = item.get("explanations") or []
        top_driver = explanations[0].get("feature") if explanations else None
        entity = reveal_entity(item.get("entity"))
        rows.append(
            {
                "id": item.get("_id"),
                "entity": entity.get("display_name") or entity.get("id"),
                "model_version": item.get("model_version"),
                "score": _round(_score(item)),
                "label": get_nested(item, "prediction.label"),
                "result": result,
                "top_driver": top_driver,
                "created_at": item.get("created_at"),
            }
        )
    false_positives = sorted([row for row in rows if row["result"] == "fp"], key=lambda row: row["score"] or 0, reverse=True)
    false_negatives = sorted([row for row in rows if row["result"] == "fn"], key=lambda row: row["score"] or 0)
    return {"false_positives": false_positives[:8], "false_negatives": false_negatives[:8]}


def _actions(
    best_threshold: dict[str, Any] | None,
    default_threshold: float,
    calibration: dict[str, Any],
    coverage: list[dict[str, Any]],
    feedback_count: int,
) -> list[dict[str, str]]:
    actions = []
    if feedback_count < 50:
        actions.append(
            {
                "severity": "high",
                "title": "Cobertura de desfecho",
                "detail": "Amostra pequena para threshold, calibracao e segmentos.",
                "i18n": {
                    "title": {"pt-BR": "Cobertura de desfecho", "en": "Outcome coverage"},
                    "detail": {
                        "pt-BR": "Amostra pequena para threshold, calibração e segmentos.",
                        "en": "Small sample for threshold, calibration, and segments.",
                    },
                },
            }
        )
    if best_threshold and abs(float(best_threshold["threshold"]) - default_threshold) >= 0.1:
        actions.append(
            {
                "severity": "medium",
                "title": "Threshold operacional",
                "detail": f"F2 online: {best_threshold['threshold']}. Padrao atual: {default_threshold}.",
                "i18n": {
                    "title": {"pt-BR": "Threshold operacional", "en": "Operational threshold"},
                    "detail": {
                        "pt-BR": f"F2 online: {best_threshold['threshold']}. Padrão atual: {default_threshold}.",
                        "en": f"Online F2: {best_threshold['threshold']}. Current default: {default_threshold}.",
                    },
                },
            }
        )
    if (calibration.get("ece") or 0) >= 0.08:
        actions.append(
            {
                "severity": "medium",
                "title": "Calibracao de score",
                "detail": "ECE acima de 0.08: score e taxa observada fora de alinhamento.",
                "i18n": {
                    "title": {"pt-BR": "Calibração de score", "en": "Score calibration"},
                    "detail": {
                        "pt-BR": "ECE acima de 0.08: score e taxa observada fora de alinhamento.",
                        "en": "ECE above 0.08: score and observed rate are misaligned.",
                    },
                },
            }
        )
    missing = [row for row in coverage if row.get("required") and (row.get("missing_rate") or 0) >= 0.05]
    if missing:
        actions.append(
            {
                "severity": "high",
                "title": "Contrato de features",
                "detail": f"{len(missing)} feature(s) obrigatoria(s) com missing rate acima de 5%.",
                "i18n": {
                    "title": {"pt-BR": "Contrato de features", "en": "Feature contract"},
                    "detail": {
                        "pt-BR": f"{len(missing)} feature(s) obrigatória(s) com missing rate acima de 5%.",
                        "en": f"{len(missing)} required feature(s) with missing rate above 5%.",
                    },
                },
            }
        )
    if not actions:
        actions.append(
            {
                "severity": "low",
                "title": "Analise avancada",
                "detail": "Priorize segmentos, erros e cobertura de features.",
                "i18n": {
                    "title": {"pt-BR": "Análise avançada", "en": "Advanced analysis"},
                    "detail": {
                        "pt-BR": "Priorize segmentos, erros e cobertura de features.",
                        "en": "Prioritize segments, errors, and feature coverage.",
                    },
                },
            }
        )
    return actions


_DIAGNOSTICS_MEMO: dict[tuple[str, str], tuple[tuple, dict[str, Any]]] = {}


async def build_model_diagnostics(store: DocumentStore, model_id: str, slice_feature: str | None = None) -> dict[str, Any]:
    from app.db.document_store import JsonDocumentStore  # local import to avoid cycle

    model = await store.find_one("models", {"_id": model_id})
    prediction_count = await store.count("predictions", {"model_id": model_id})
    feedback_count = await store.count("predictions", {"model_id": model_id, "feedback.available": True})
    requested_slice = slice_feature or "__auto__"
    cache_key = (DIAGNOSTIC_CACHE_VERSION, prediction_count, feedback_count)

    memo = _DIAGNOSTICS_MEMO.get((model_id, requested_slice))
    if memo and memo[0] == cache_key:
        diagnostics = dict(memo[1])
        diagnostics["generated_at"] = utcnow()
        return diagnostics

    use_json_store = isinstance(store, JsonDocumentStore)
    if not use_json_store:
        cached = await store.find_one(
            "diagnostic_cache",
            {
                "model_id": model_id,
                "slice_feature": requested_slice,
                "cache_version": DIAGNOSTIC_CACHE_VERSION,
                "prediction_count": prediction_count,
                "feedback_count": feedback_count,
            },
        )
        if cached:
            diagnostics = cached["diagnostics"]
            diagnostics["generated_at"] = utcnow()
            _DIAGNOSTICS_MEMO[(model_id, requested_slice)] = (cache_key, diagnostics)
            return diagnostics

    predictions = await store.find_many("predictions", {"model_id": model_id}, sort=[("created_at", -1)], limit=0)
    model = model or {}
    positive_label = get_nested(model, "labels.positive", "positive")
    default_threshold = float(model.get("default_threshold", 0.5) or 0.5)
    all_scores = [_score(item) for item in predictions]
    scored_feedback = [(_score(item), actual) for item in predictions if (actual := _actual_positive(item)) is not None]

    threshold_curve = [_threshold_metrics(scored_feedback, all_scores, threshold) for threshold in THRESHOLDS]
    valid_f2 = [row for row in threshold_curve if row.get("f2") is not None]
    best_threshold = max(valid_f2, key=lambda row: row["f2"]) if valid_f2 else None
    calibration = _calibration(scored_feedback)
    coverage = _feature_coverage(model, predictions)
    candidates = _candidate_features(model, predictions)
    selected_slice = slice_feature or (candidates[0]["feature"] if candidates else "")
    slices = _slice_rows(predictions, selected_slice, positive_label) if selected_slice else []
    errors = _error_examples(predictions)

    diagnostics = {
        "model_id": model_id,
        "project_id": model.get("project_id"),
        "generated_at": utcnow(),
        "summary": {
            "prediction_count": prediction_count,
            "feedback_count": feedback_count,
            "feedback_rate": _round(feedback_count / prediction_count if prediction_count else 0),
            "default_threshold": default_threshold,
            "recommended_threshold": best_threshold["threshold"] if best_threshold else default_threshold,
            "best_f2": best_threshold.get("f2") if best_threshold else None,
            "ece": calibration.get("ece"),
            "brier_score": calibration.get("brier_score"),
            "positive_label": positive_label,
        },
        "threshold_curve": threshold_curve,
        "recommendations": {
            "best_f2": best_threshold,
            "actions": _actions(best_threshold, default_threshold, calibration, coverage, feedback_count),
        },
        "calibration": calibration,
        "feature_importance": _feature_importance(predictions),
        "feature_coverage": coverage,
        "slice_candidates": candidates,
        "slice_feature": selected_slice,
        "slice_diagnostics": slices,
        "error_analysis": errors,
        "notebook_pack": {
            "title": f"ModelTrace diagnostics for {model.get('name', model_id)}",
            "cells": [
                {
                    "type": "markdown",
                    "content": "## ModelTrace diagnostics\nPacote para reproduzir threshold, calibracao e segmentos.",
                },
                {
                    "type": "code",
                    "content": "import pandas as pd\n# Carregue o CSV exportado e compare experimentos locais com o comportamento online.",
                },
            ],
        },
        "methodological_notes": [
            "Threshold e calibracao usam predicoes com feedback real.",
            "Segmentos indicam diferencas operacionais, nao causalidade.",
            "Feature importance usa explicacoes online e deve ser validada offline.",
        ],
    }
    _DIAGNOSTICS_MEMO[(model_id, requested_slice)] = (cache_key, dict(diagnostics))
    if not use_json_store:
        await store.upsert_one(
            "diagnostic_cache",
            {"model_id": model_id, "slice_feature": requested_slice},
            {
                "_id": f"diag_{model_id}_{requested_slice}",
                "model_id": model_id,
                "project_id": model.get("project_id"),
                "org_id": model.get("org_id"),
                "slice_feature": requested_slice,
                "cache_version": DIAGNOSTIC_CACHE_VERSION,
                "prediction_count": prediction_count,
                "feedback_count": feedback_count,
                "diagnostics": diagnostics,
                "computed_at": utcnow(),
            },
        )
    return diagnostics
