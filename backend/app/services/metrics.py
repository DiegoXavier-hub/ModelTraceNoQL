from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from math import log
from statistics import mean, pstdev
from typing import Any

from app.core.utils import get_nested, utcnow
from app.db.document_store import DocumentStore, JsonDocumentStore


# In-memory dashboard cache used to bypass the JsonDocumentStore _save() penalty
# on the hot path. Keyed by (project_id, cache_version, prediction_count, alert_count).
# Restarting the process drops this cache, but the data store is read-only at boot
# so the next call simply recomputes. For MongoDB-backed stores we keep the
# persistent dashboard_cache collection as well (writes are cheap there).
_DASHBOARD_MEMO: dict[str, tuple[tuple, dict[str, Any]]] = {}


SCORE_BUCKETS = [
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

DASHBOARD_CACHE_VERSION = 2


def _date_label(value: str) -> str:
    return value[:10]


def _histogram(scores: list[float]) -> list[dict[str, Any]]:
    buckets = []
    for start, end in SCORE_BUCKETS:
        count = sum(1 for score in scores if start <= score < end)
        buckets.append({"bucket": f"{start:.1f}-{min(end, 1.0):.1f}", "count": count})
    return buckets


def _confusion_matrix(predictions: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter(get_nested(item, "feedback.classification_result") for item in predictions)
    return {key: int(counter.get(key, 0)) for key in ["tp", "fp", "tn", "fn"]}


def _performance_from_cm(cm: dict[str, int]) -> dict[str, float | None]:
    tp, fp, tn, fn = cm["tp"], cm["fp"], cm["tn"], cm["fn"]
    total = tp + fp + tn + fn
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    accuracy = (tp + tn) / total if total else None
    f1 = (2 * precision * recall / (precision + recall)) if precision and recall else None
    return {
        "accuracy": round(accuracy, 4) if accuracy is not None else None,
        "precision": round(precision, 4) if precision is not None else None,
        "recall": round(recall, 4) if recall is not None else None,
        "f1": round(f1, 4) if f1 is not None else None,
    }


async def recompute_model_metrics(store: DocumentStore, model_id: str) -> list[dict[str, Any]]:
    model = await store.find_one("models", {"_id": model_id})
    positive_label = get_nested(model or {}, "labels.positive", "high_risk")
    predictions = await store.find_many("predictions", {"model_id": model_id}, limit=0)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in predictions:
        grouped[(_date_label(item["created_at"]), item.get("model_version", "unknown"))].append(item)

    snapshots = []
    await store.delete_many("metrics_snapshots", {"model_id": model_id})
    for (day, version), items in grouped.items():
        scores = [float(get_nested(item, "prediction.score", 0)) for item in items]
        labels = [get_nested(item, "prediction.label") for item in items]
        with_feedback = [item for item in items if get_nested(item, "feedback.available")]
        cm = _confusion_matrix(with_feedback)
        snapshot = {
            "_id": f"metric_day_{day.replace('-', '')}_{model_id}_{version.replace('.', '').replace('-', '')}",
            "project_id": items[0]["project_id"],
            "org_id": items[0]["org_id"],
            "model_id": model_id,
            "model_version": version,
            "period": {
                "granularity": "day",
                "start": f"{day}T00:00:00Z",
                "end": f"{day}T23:59:59Z",
                "label": day,
            },
            "counts": {
                "total": len(items),
                "positive": sum(1 for label in labels if label == positive_label),
                "negative": sum(1 for label in labels if label != positive_label),
                "with_feedback": len(with_feedback),
                "without_feedback": len(items) - len(with_feedback),
            },
            "performance": _performance_from_cm(cm),
            "confusion_matrix": cm,
            "score_distribution": {
                "mean": round(mean(scores), 4) if scores else None,
                "std": round(pstdev(scores), 4) if len(scores) > 1 else 0,
                "histogram": _histogram(scores),
            },
            "computed_at": utcnow(),
        }
        await store.upsert_one("metrics_snapshots", {"_id": snapshot["_id"]}, snapshot)
        snapshots.append(snapshot)
    return snapshots


async def build_project_dashboard(store: DocumentStore, project_id: str) -> dict[str, Any]:
    project = await store.find_one("projects", {"_id": project_id})
    positive_label = (
        get_nested(project or {}, "settings.positive_label")
        or get_nested(project or {}, "labels.positive")
    )
    if not positive_label:
        models = await store.find_many("models", {"project_id": project_id}, limit=1)
        positive_label = get_nested(models[0], "labels.positive") if models else None
    positive_label = positive_label or "high_risk"
    prediction_count = await store.count("predictions", {"project_id": project_id})
    alerts = await store.find_many("alerts", {"project_id": project_id, "status": {"$ne": "resolved"}}, limit=100)
    cache_key = (DASHBOARD_CACHE_VERSION, prediction_count, len(alerts))

    # Process-local memo first: avoids both reading and writing the on-disk
    # dashboard_cache (which costs a full ~200 MB rewrite on JsonDocumentStore).
    memo = _DASHBOARD_MEMO.get(project_id)
    if memo and memo[0] == cache_key:
        dashboard = dict(memo[1])
        dashboard["generated_at"] = utcnow()
        return dashboard

    use_json_store = isinstance(store, JsonDocumentStore)
    if not use_json_store:
        cached = await store.find_one(
            "dashboard_cache",
            {
                "project_id": project_id,
                "cache_version": DASHBOARD_CACHE_VERSION,
                "prediction_count": prediction_count,
                "alert_count": len(alerts),
            },
        )
        if cached:
            dashboard = cached["dashboard"]
            dashboard["generated_at"] = utcnow()
            _DASHBOARD_MEMO[project_id] = (cache_key, dashboard)
            return dashboard

    predictions = await store.find_many("predictions", {"project_id": project_id}, sort=[("created_at", -1)], limit=0)
    scores = [float(get_nested(item, "prediction.score", 0)) for item in predictions]
    with_feedback = [item for item in predictions if get_nested(item, "feedback.available")]
    cm = _confusion_matrix(with_feedback)

    by_day: dict[str, int] = defaultdict(int)
    by_version: dict[str, dict[str, Any]] = defaultdict(lambda: {"predictions": 0, "entities": set(), "feedback": 0})
    for item in predictions:
        by_day[_date_label(item["created_at"])] += 1
        version = item.get("model_version", "unknown")
        by_version[version]["predictions"] += 1
        if get_nested(item, "entity.id"):
            by_version[version]["entities"].add(get_nested(item, "entity.id"))
        if get_nested(item, "feedback.available"):
            by_version[version]["feedback"] += 1

    latest_critical = [
        item
        for item in predictions
        if get_nested(item, "flags.is_critical")
        or get_nested(item, "prediction.label") == positive_label
        or float(get_nested(item, "prediction.score", 0)) >= 0.85
    ][:10]
    positive_count = sum(1 for item in predictions if get_nested(item, "prediction.label") == positive_label)
    positive_rate = round(positive_count / len(predictions), 4) if predictions else 0

    dashboard = {
        "project_id": project_id,
        "generated_at": utcnow(),
        "kpis": {
            "total_predictions": len(predictions),
            "high_risk_rate": positive_rate,
            "actionable_rate": positive_rate,
            "positive_label": positive_label,
            "feedback_rate": round(len(with_feedback) / len(predictions), 4) if predictions else 0,
            "avg_score": round(mean(scores), 4) if scores else 0,
            "active_alerts": len(alerts),
        },
        "performance": _performance_from_cm(cm),
        "confusion_matrix": cm,
        "score_histogram": _histogram(scores),
        "volume_series": [{"date": key, "count": by_day[key]} for key in sorted(by_day)],
        "version_summary": [
            {
                "window": str(version).upper(),
                "value": str(version),
                "predictions": int(values["predictions"]),
                "entities": len(values["entities"]),
                "feedback": int(values["feedback"]),
            }
            for version, values in sorted(by_version.items(), key=lambda item: item[1]["predictions"], reverse=True)
        ],
        "latest_critical": latest_critical,
        "alerts": alerts,
    }
    _DASHBOARD_MEMO[project_id] = (cache_key, dict(dashboard))
    if not use_json_store:
        await store.upsert_one(
            "dashboard_cache",
            {"project_id": project_id},
            {
                "_id": f"dash_{project_id}",
                "project_id": project_id,
                "org_id": (project or {}).get("org_id"),
                "cache_version": DASHBOARD_CACHE_VERSION,
                "prediction_count": prediction_count,
                "alert_count": len(alerts),
                "dashboard": dashboard,
                "computed_at": utcnow(),
            },
        )
    return dashboard


def _psi(reference: list[float], current: list[float]) -> float:
    if not reference or not current:
        return 0.0
    value = 0.0
    for start, end in SCORE_BUCKETS:
        ref_pct = max(sum(1 for item in reference if start <= item < end) / len(reference), 0.0001)
        cur_pct = max(sum(1 for item in current if start <= item < end) / len(current), 0.0001)
        value += (cur_pct - ref_pct) * log(cur_pct / ref_pct)
    return round(value, 4)


def _psi_continuous(reference: list[float], current: list[float], bins: int = 8) -> float:
    """PSI calculado em quantis igualitarios da serie de referencia.

    Funciona para qualquer feature continua (sem assumir intervalo [0, 1]).
    Retorna 0.0 se houver menos de ``bins`` pontos validos em alguma das duas series.
    """
    if not reference or not current or len(reference) < bins or len(current) < bins:
        return 0.0
    sorted_ref = sorted(reference)
    edges: list[float] = [sorted_ref[int(round(quantile * (len(sorted_ref) - 1)))]
                          for quantile in [index / bins for index in range(1, bins)]]
    cuts = [-float("inf"), *edges, float("inf")]
    value = 0.0
    for index in range(len(cuts) - 1):
        low = cuts[index]
        high = cuts[index + 1]
        ref_pct = max(sum(1 for item in reference if low <= item < high) / len(reference), 0.0001)
        cur_pct = max(sum(1 for item in current if low <= item < high) / len(current), 0.0001)
        value += (cur_pct - ref_pct) * log(cur_pct / ref_pct)
    return round(value, 4)


def drift_status_from_psi(psi: float) -> str:
    if psi >= 0.25:
        return "drift_detected"
    if psi >= 0.10:
        return "attention"
    return "stable"


async def generate_drift_report(store: DocumentStore, model_id: str) -> dict[str, Any]:
    predictions = await store.find_many("predictions", {"model_id": model_id}, sort=[("created_at", 1)], limit=0)
    if len(predictions) < 10:
        report = {
            "_id": f"drift_{model_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "model_id": model_id,
            "status": "insufficient_data",
            "message": "Minimo de 10 predicoes para calcular drift.",
            "created_at": utcnow(),
        }
        await store.insert_one("drift_reports", report)
        return report

    midpoint = len(predictions) // 2
    reference = predictions[:midpoint]
    current = predictions[midpoint:]
    ref_scores = [float(get_nested(item, "prediction.score", 0)) for item in reference]
    cur_scores = [float(get_nested(item, "prediction.score", 0)) for item in current]
    score_psi = _psi(ref_scores, cur_scores)

    feature_rows = []
    feature_names = set()
    for item in predictions:
        feature_names.update((item.get("features") or {}).keys())
    for feature in sorted(feature_names):
        ref_values = [get_nested(item, f"features.{feature}") for item in reference]
        cur_values = [get_nested(item, f"features.{feature}") for item in current]
        if all(isinstance(value, (int, float)) for value in ref_values + cur_values if value is not None):
            ref_numeric = [float(value) for value in ref_values if value is not None]
            cur_numeric = [float(value) for value in cur_values if value is not None]
            delta = (mean(cur_numeric) - mean(ref_numeric)) if ref_numeric and cur_numeric else 0
            feature_psi = _psi_continuous(ref_numeric, cur_numeric)
            feature_rows.append(
                {
                    "name": feature,
                    "type": "continuous",
                    "mean_ref": round(mean(ref_numeric), 4) if ref_numeric else None,
                    "mean_cur": round(mean(cur_numeric), 4) if cur_numeric else None,
                    "delta": round(delta, 4),
                    "psi": feature_psi,
                    "status": drift_status_from_psi(feature_psi)
                    if feature_psi
                    else ("attention" if abs(delta) > 0.1 else "stable"),
                }
            )

    report = {
        "_id": f"drift_{model_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "project_id": predictions[0]["project_id"],
        "org_id": predictions[0]["org_id"],
        "model_id": model_id,
        "model_version": predictions[-1].get("model_version"),
        "reference_period": {
            "start": reference[0]["created_at"],
            "end": reference[-1]["created_at"],
            "count": len(reference),
        },
        "current_period": {
            "start": current[0]["created_at"],
            "end": current[-1]["created_at"],
            "count": len(current),
        },
        "prediction_drift": {
            "psi": score_psi,
            "mean_score_ref": round(mean(ref_scores), 4),
            "mean_score_cur": round(mean(cur_scores), 4),
            "status": "drift_detected" if score_psi >= 0.25 else "attention" if score_psi >= 0.1 else "stable",
        },
        "data_drift": {"features": feature_rows},
        "created_at": utcnow(),
    }
    await store.insert_one("drift_reports", report)
    return report
