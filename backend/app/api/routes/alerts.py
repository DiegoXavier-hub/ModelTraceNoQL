from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_store, require_same_org
from app.core.privacy import audit_actor_for_user
from app.core.utils import get_nested, make_id, utcnow
from app.db.document_store import DocumentStore
from app.schemas import AlertRulePayload, AlertRuleUpdate
from app.services.audit import create_audit_event
from app.services.metrics import recompute_model_metrics
from app.services.notifications import create_notification

router = APIRouter(tags=["alerts"])


def _violates(value: float | int | None, operator: str, threshold: float) -> bool:
    if value is None:
        return False
    return value < threshold if operator == "less_than" else value > threshold


def _alert_message(rule: dict, value: float | int | None, detail: str = "") -> str:
    value_text = "n/a" if value is None else round(float(value), 4)
    base = f"{rule['metric']}={value_text} / {rule['operator']} {rule['threshold']}"
    return f"{base}. {detail}".strip()


def _alert_i18n(rule: dict, message: str) -> dict:
    existing = rule.get("i18n") or {}
    title_pt = existing.get("title", {}).get("pt-BR") or existing.get("name", {}).get("pt-BR") or rule["name"]
    title_en = existing.get("title", {}).get("en") or existing.get("name", {}).get("en") or rule["name"]
    message_pt = existing.get("message", {}).get("pt-BR") or message
    message_en = existing.get("message", {}).get("en") or message
    return {
        "title": {"pt-BR": title_pt, "en": title_en},
        "message": {"pt-BR": message_pt, "en": message_en},
    }


async def _open_alert_exists(store: DocumentStore, rule: dict) -> bool:
    existing = await store.find_one(
        "alerts",
        {
            "project_id": rule["project_id"],
            "rule_id": rule["_id"],
            "status": {"$ne": "resolved"},
        },
    )
    return existing is not None


async def _create_rule_alert(store: DocumentStore, rule: dict, value: float | int | None, detail: str = "") -> dict | None:
    if await _open_alert_exists(store, rule):
        return None
    message = _alert_message(rule, value, detail)
    alert = {
        "_id": make_id("alert"),
        "org_id": rule["org_id"],
        "project_id": rule["project_id"],
        "model_id": rule.get("model_id"),
        "rule_id": rule["_id"],
        "title": rule["name"],
        "type": rule["type"],
        "severity": rule["severity"],
        "status": "open",
        "message": message,
        "i18n": _alert_i18n(rule, message),
        "metric": rule["metric"],
        "observed_value": value,
        "threshold": rule["threshold"],
        "created_at": utcnow(),
    }
    await store.insert_one("alerts", alert)
    await store.update_one("projects", {"_id": rule["project_id"]}, {"$inc": {"stats.active_alerts": 1}})
    project = await store.find_one("projects", {"_id": rule["project_id"]})
    await create_notification(
        store,
        org_id=rule["org_id"],
        user_id=(project or {}).get("owner_id"),
        project_id=rule["project_id"],
        type_="alert.created",
        title=alert["title"],
        message=alert["message"],
        severity=alert["severity"],
        link={"view": "operations", "resource_id": alert["_id"]},
        metadata={"alert_id": alert["_id"], "rule_id": rule["_id"]},
    )
    return alert


async def _latest_snapshot_metric(store: DocumentStore, rule: dict) -> tuple[float | None, str]:
    snapshots = await store.find_many(
        "metrics_snapshots", {"model_id": rule["model_id"]}, sort=[("period.start", -1)], limit=1
    )
    if not snapshots:
        snapshots = await recompute_model_metrics(store, rule["model_id"])
        snapshots = sorted(snapshots, key=lambda item: get_nested(item, "period.start", ""), reverse=True)[:1]
    if not snapshots:
        return None, "Sem snapshot de metricas."
    snapshot = snapshots[0]
    feedback_count = int(get_nested(snapshot, "counts.with_feedback", 0) or 0)
    if feedback_count < int(rule.get("min_feedback_count", 1)):
        return None, f"Feedback abaixo do minimo da regra ({feedback_count})."
    metric_value = get_nested(snapshot, f"performance.{rule['metric']}")
    return metric_value, f"Snapshot {get_nested(snapshot, 'period.label', 'atual')}."


async def _feedback_rate(store: DocumentStore, rule: dict) -> tuple[float | None, str]:
    filter_ = {"project_id": rule["project_id"]}
    if rule.get("model_id"):
        filter_["model_id"] = rule["model_id"]
    total = await store.count("predictions", filter_)
    if total == 0:
        return None, "Sem predicoes."
    with_feedback = await store.count("predictions", {**filter_, "feedback.available": True})
    return round(with_feedback / total, 4), f"{with_feedback}/{total} predicoes com feedback."


async def _volume_ratio(store: DocumentStore, rule: dict) -> tuple[float | None, str]:
    filter_ = {"project_id": rule["project_id"]}
    if rule.get("model_id"):
        filter_["model_id"] = rule["model_id"]
    predictions = await store.find_many("predictions", filter_, sort=[("created_at", 1)], limit=0)
    if len(predictions) < 10:
        return None, "Amostra pequena para volume."
    midpoint = len(predictions) // 2
    reference = max(midpoint, 1)
    current = len(predictions) - midpoint
    return round(current / reference, 4), f"Atual {current}; referencia {reference}."


async def _prediction_drift(store: DocumentStore, rule: dict) -> tuple[float | None, str]:
    reports = await store.find_many("drift_reports", {"model_id": rule["model_id"]}, sort=[("created_at", -1)], limit=1)
    if not reports:
        return None, "Sem relatorio de drift."
    report = reports[0]
    value = get_nested(report, f"prediction_drift.{rule['metric']}", get_nested(report, "prediction_drift.psi"))
    status_ = get_nested(report, "prediction_drift.status", "n/a")
    return value, f"Status {status_}."


async def _data_drift(store: DocumentStore, rule: dict) -> tuple[float | None, str]:
    reports = await store.find_many("drift_reports", {"model_id": rule["model_id"]}, sort=[("created_at", -1)], limit=1)
    if not reports:
        return None, "Sem relatorio de drift."
    features = get_nested(reports[0], "data_drift.features", []) or []
    if rule["metric"] == "feature_attention_count":
        value = sum(1 for item in features if item.get("status") != "stable")
    else:
        value = max((abs(float(item.get("delta", 0) or 0)) for item in features), default=0)
    return value, f"{len(features)} features avaliadas."


async def _missing_feature_rate(store: DocumentStore, rule: dict) -> tuple[float | None, str]:
    model = await store.find_one("models", {"_id": rule["model_id"]})
    expected_features = (model or {}).get("expected_features", [])
    expected = [item for item in expected_features if item.get("required")]
    if not expected and expected_features:
        expected = expected_features
    if not expected:
        expected = [{"name": name, "required": True} for name in (model or {}).get("features", [])]
    if not expected:
        return None, "Modelo sem contrato de features obrigatorias."
    predictions = await store.find_many("predictions", {"model_id": rule["model_id"]}, limit=0)
    if not predictions:
        return None, "Sem predicoes."
    missing = 0
    total_checks = len(predictions) * len(expected)
    for prediction in predictions:
        features = prediction.get("features") or {}
        for feature in expected:
            value = features.get(feature.get("name"))
            if value in (None, ""):
                missing += 1
    return round(missing / max(total_checks, 1), 4), f"{missing}/{total_checks} checks ausentes."


async def _deprecated_version_count(store: DocumentStore, rule: dict) -> tuple[float | None, str]:
    deprecated = await store.find_many("model_versions", {"model_id": rule["model_id"], "status": "deprecated"}, limit=0)
    versions = [item["version"] for item in deprecated]
    if not versions:
        return 0, "Sem versoes deprecated."
    count = await store.count("predictions", {"model_id": rule["model_id"], "model_version": {"$in": versions}})
    return count, f"Versoes: {', '.join(versions[:4])}."


async def _evaluate_rule(store: DocumentStore, rule: dict) -> tuple[float | None, str]:
    if rule["type"] == "performance_threshold":
        return await _latest_snapshot_metric(store, rule)
    if rule["type"] == "feedback_rate_low":
        return await _feedback_rate(store, rule)
    if rule["type"] == "volume_drop":
        return await _volume_ratio(store, rule)
    if rule["type"] == "prediction_drift":
        return await _prediction_drift(store, rule)
    if rule["type"] == "data_drift":
        return await _data_drift(store, rule)
    if rule["type"] == "missing_features":
        return await _missing_feature_rate(store, rule)
    if rule["type"] == "deprecated_version_active":
        return await _deprecated_version_count(store, rule)
    return None, "Tipo de regra sem avaliador."


async def _default_project_rules(store: DocumentStore, project_id: str, org_id: str) -> list[dict]:
    models = await store.find_many("models", {"project_id": project_id, "status": "active"}, limit=200)
    rules = []
    for model in models:
        model_id = model["_id"]
        base = {"org_id": org_id, "project_id": project_id, "model_id": model_id, "enabled": True, "min_feedback_count": 1}
        rules.extend(
            [
                {
                    **base,
                    "_id": f"default_feedback_rate_low_{model_id}",
                    "name": "Cobertura de feedback baixa",
                    "i18n": {
                        "name": {"pt-BR": "Cobertura de feedback baixa", "en": "Low feedback coverage"},
                        "title": {"pt-BR": "Cobertura de feedback baixa", "en": "Low feedback coverage"},
                    },
                    "type": "feedback_rate_low",
                    "metric": "feedback_rate",
                    "operator": "less_than",
                    "threshold": 0.25,
                    "severity": "medium",
                },
                {
                    **base,
                    "_id": f"default_missing_features_{model_id}",
                    "name": "Features obrigatorias ausentes",
                    "i18n": {
                        "name": {"pt-BR": "Features obrigatórias ausentes", "en": "Missing required features"},
                        "title": {"pt-BR": "Features obrigatórias ausentes", "en": "Missing required features"},
                    },
                    "type": "missing_features",
                    "metric": "missing_rate",
                    "operator": "greater_than",
                    "threshold": 0.05,
                    "severity": "high",
                },
                {
                    **base,
                    "_id": f"default_deprecated_version_active_{model_id}",
                    "name": "Versao deprecated em uso",
                    "i18n": {
                        "name": {"pt-BR": "Versão deprecated em uso", "en": "Deprecated version in use"},
                        "title": {"pt-BR": "Versão deprecated em uso", "en": "Deprecated version in use"},
                    },
                    "type": "deprecated_version_active",
                    "metric": "deprecated_predictions",
                    "operator": "greater_than",
                    "threshold": 0,
                    "severity": "medium",
                },
                {
                    **base,
                    "_id": f"default_prediction_drift_{model_id}",
                    "name": "Drift de score",
                    "i18n": {
                        "name": {"pt-BR": "Drift de score", "en": "Score drift"},
                        "title": {"pt-BR": "Drift de score", "en": "Score drift"},
                    },
                    "type": "prediction_drift",
                    "metric": "psi",
                    "operator": "greater_than",
                    "threshold": 0.1,
                    "severity": "medium",
                },
                {
                    **base,
                    "_id": f"default_data_drift_{model_id}",
                    "name": "Drift de features",
                    "i18n": {
                        "name": {"pt-BR": "Drift de features", "en": "Feature drift"},
                        "title": {"pt-BR": "Drift de features", "en": "Feature drift"},
                    },
                    "type": "data_drift",
                    "metric": "feature_attention_count",
                    "operator": "greater_than",
                    "threshold": 0,
                    "severity": "medium",
                },
            ]
        )
    return rules


@router.get("/alert-rules")
async def list_alert_rules(
    project_id: str | None = None,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    filter_ = {"org_id": user["org_id"]}
    if project_id:
        filter_["project_id"] = project_id
    rules = await store.find_many("alert_rules", filter_, sort=[("created_at", -1)], limit=200)
    return {"items": rules}


@router.post("/alert-rules", status_code=201)
async def create_alert_rule(
    payload: AlertRulePayload,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_same_org(await store.find_one("projects", {"_id": payload.project_id}), user)
    rule = {
        "_id": make_id("rule"),
        "org_id": user["org_id"],
        "project_id": payload.project_id,
        "model_id": payload.model_id,
        **payload.model_dump(),
        "created_by": user["_id"],
        "created_at": utcnow(),
    }
    await store.insert_one("alert_rules", rule)
    await create_audit_event(
        store,
        org_id=user["org_id"],
        project_id=payload.project_id,
        actor=audit_actor_for_user(user),
        event_type="alert_rule.created",
        resource_type="alert_rule",
        resource_id=rule["_id"],
        diff={"after": rule},
    )
    return rule


@router.patch("/alert-rules/{rule_id}")
async def update_alert_rule(
    rule_id: str,
    payload: AlertRuleUpdate,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    before = require_same_org(await store.find_one("alert_rules", {"_id": rule_id}), user)
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        return before
    updates["updated_at"] = utcnow()
    await store.update_one("alert_rules", {"_id": rule_id}, {"$set": updates})
    after = await store.find_one("alert_rules", {"_id": rule_id})
    await create_audit_event(
        store,
        org_id=user["org_id"],
        project_id=before["project_id"],
        actor=audit_actor_for_user(user),
        event_type="alert_rule.updated",
        resource_type="alert_rule",
        resource_id=rule_id,
        diff={"before": before, "after": after},
    )
    return after or before


@router.delete("/alert-rules/{rule_id}")
async def delete_alert_rule(
    rule_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    rule = require_same_org(await store.find_one("alert_rules", {"_id": rule_id}), user)
    await store.delete_one("alert_rules", {"_id": rule_id})
    await create_audit_event(
        store,
        org_id=user["org_id"],
        project_id=rule["project_id"],
        actor=audit_actor_for_user(user),
        event_type="alert_rule.deleted",
        resource_type="alert_rule",
        resource_id=rule_id,
        diff={"before": rule},
    )
    return {"status": "deleted", "rule_id": rule_id}


@router.get("/alerts")
async def list_alerts(
    project_id: str | None = None,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    filter_ = {"org_id": user["org_id"]}
    if project_id:
        filter_["project_id"] = project_id
    alerts = await store.find_many("alerts", filter_, sort=[("created_at", -1)], limit=200)
    return {"items": alerts}


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    alert = require_same_org(await store.find_one("alerts", {"_id": alert_id}), user)
    await store.update_one(
        "alerts",
        {"_id": alert_id},
        {"$set": {"status": "acknowledged", "acknowledged_by": user["_id"], "acknowledged_at": utcnow()}},
    )
    return await store.find_one("alerts", {"_id": alert_id}) or alert


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    alert = require_same_org(await store.find_one("alerts", {"_id": alert_id}), user)
    await store.update_one(
        "alerts",
        {"_id": alert_id},
        {"$set": {"status": "resolved", "resolved_by": user["_id"], "resolved_at": utcnow()}},
    )
    if alert.get("status") != "resolved":
        project = await store.find_one("projects", {"_id": alert["project_id"]})
        active_alerts = max(0, int(get_nested(project or {}, "stats.active_alerts", 0) or 0) - 1)
        await store.update_one("projects", {"_id": alert["project_id"]}, {"$set": {"stats.active_alerts": active_alerts}})
    return await store.find_one("alerts", {"_id": alert_id}) or alert


@router.post("/alerts/run-checks")
async def run_alert_checks(
    project_id: str,
    include_defaults: bool = False,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_same_org(await store.find_one("projects", {"_id": project_id}), user)
    rules = await store.find_many("alert_rules", {"project_id": project_id, "enabled": True}, limit=200)
    if include_defaults:
        existing_ids = {rule["_id"] for rule in rules}
        rules.extend([rule for rule in await _default_project_rules(store, project_id, user["org_id"]) if rule["_id"] not in existing_ids])
    created = []
    evaluated = []
    for rule in rules:
        value, detail = await _evaluate_rule(store, rule)
        violated = _violates(value, rule["operator"], float(rule["threshold"]))
        evaluated.append(
            {
                "rule_id": rule["_id"],
                "type": rule["type"],
                "metric": rule["metric"],
                "value": value,
                "violated": violated,
                "detail": detail,
            }
        )
        if not violated:
            continue
        alert = await _create_rule_alert(store, rule, value, detail)
        if alert:
            created.append(alert)
    if created:
        await create_audit_event(
            store,
            org_id=user["org_id"],
            project_id=project_id,
            actor=audit_actor_for_user(user),
            event_type="alerts.checked",
            resource_type="project",
            resource_id=project_id,
            diff={"after": {"created": len(created), "evaluated": len(evaluated)}},
        )
    return {"created": created, "evaluated": evaluated}
