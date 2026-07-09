from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user, get_store, require_same_org
from app.core.privacy import audit_actor_for_user
from app.core.utils import make_id, slugify, utcnow
from app.db.document_store import DocumentStore
from app.schemas import MLModelCreate, ModelVersionCreate
from app.services.audit import create_audit_event
from app.services.diagnostics import build_model_diagnostics
from app.services.metrics import generate_drift_report, recompute_model_metrics

router = APIRouter(tags=["models"])


@router.get("/projects/{project_id}/models")
async def list_models(
    project_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_same_org(await store.find_one("projects", {"_id": project_id}), user)
    models = await store.find_many("models", {"project_id": project_id}, sort=[("created_at", -1)], limit=200)
    return {"items": models}


@router.post("/projects/{project_id}/models", status_code=201)
async def create_model(
    project_id: str,
    payload: MLModelCreate,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    project = require_same_org(await store.find_one("projects", {"_id": project_id}), user)
    model = {
        "_id": make_id("model"),
        "project_id": project_id,
        "org_id": user["org_id"],
        "name": payload.name,
        "slug": slugify(payload.name),
        "description": payload.description,
        "i18n": payload.i18n,
        "problem_type": payload.problem_type,
        "target_name": payload.target_name,
        "labels": payload.labels,
        "default_threshold": payload.default_threshold,
        "primary_metric": payload.primary_metric,
        "expected_features": payload.expected_features,
        "production_version_id": None,
        "created_by": user["_id"],
        "created_at": utcnow(),
        "status": "active",
    }
    await store.insert_one("models", model)
    await store.update_one("projects", {"_id": project_id}, {"$inc": {"stats.total_models": 1}})
    await create_audit_event(
        store,
        org_id=user["org_id"],
        project_id=project_id,
        actor=audit_actor_for_user(user),
        event_type="model.created",
        resource_type="model",
        resource_id=model["_id"],
        diff={"after": model},
    )
    return model


@router.get("/models/{model_id}")
async def get_model(
    model_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    return require_same_org(await store.find_one("models", {"_id": model_id}), user)


@router.get("/models/{model_id}/versions")
async def list_versions(
    model_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    model = require_same_org(await store.find_one("models", {"_id": model_id}), user)
    versions = await store.find_many("model_versions", {"model_id": model["_id"]}, sort=[("created_at", -1)], limit=200)
    return {"items": versions}


@router.post("/models/{model_id}/versions", status_code=201)
async def create_version(
    model_id: str,
    payload: ModelVersionCreate,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    model = require_same_org(await store.find_one("models", {"_id": model_id}), user)
    existing = await store.find_one("model_versions", {"model_id": model_id, "version": payload.version})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Version already exists")
    if payload.status == "production":
        current = await store.find_one("model_versions", {"model_id": model_id, "status": "production"})
        if current:
            await store.update_one(
                "model_versions",
                {"_id": current["_id"]},
                {"$set": {"status": "deprecated", "deprecated_at": utcnow()}},
            )
    version = {
        "_id": make_id("version"),
        "model_id": model_id,
        "project_id": model["project_id"],
        "org_id": user["org_id"],
        "version": payload.version,
        "algorithm": payload.algorithm,
        "status": payload.status,
        "created_by": user["_id"],
        "created_at": utcnow(),
        "promoted_to_production_at": utcnow() if payload.status == "production" else None,
        "deprecated_at": None,
        "features": payload.features,
        "hyperparameters": payload.hyperparameters,
        "training_metadata": payload.training_metadata,
        "offline_metrics": payload.offline_metrics,
        "changelog": payload.changelog,
        "notes": payload.notes,
    }
    await store.insert_one("model_versions", version)
    if payload.status == "production":
        await store.update_one("models", {"_id": model_id}, {"$set": {"production_version_id": version["_id"]}})
    await create_audit_event(
        store,
        org_id=user["org_id"],
        project_id=model["project_id"],
        actor=audit_actor_for_user(user),
        event_type="model_version.created",
        resource_type="model_version",
        resource_id=version["_id"],
        diff={"after": version},
    )
    return version


@router.get("/models/{model_id}/metrics")
async def model_metrics(
    model_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_same_org(await store.find_one("models", {"_id": model_id}), user)
    snapshots = await store.find_many("metrics_snapshots", {"model_id": model_id}, sort=[("period.start", -1)], limit=365)
    if not snapshots:
        snapshots = await recompute_model_metrics(store, model_id)
    return {"items": snapshots}


@router.get("/models/{model_id}/diagnostics")
async def model_diagnostics(
    model_id: str,
    slice_feature: str | None = None,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_same_org(await store.find_one("models", {"_id": model_id}), user)
    return await build_model_diagnostics(store, model_id, slice_feature)


@router.post("/models/{model_id}/versions/{version}/promote")
async def promote_version(
    model_id: str,
    version: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    """Promove uma versao para production.

    Demove a versao atual de production para deprecated, marca a nova como
    production, atualiza ``production_version_id`` no modelo e registra um
    evento de auditoria. Idempotente quando a versao ja eh production.
    """
    model = require_same_org(await store.find_one("models", {"_id": model_id}), user)
    target = await store.find_one(
        "model_versions", {"model_id": model_id, "version": version}
    )
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found for this model",
        )
    if target.get("status") == "production":
        return {
            "model_id": model_id,
            "promoted_version": target.get("version"),
            "previous_version": None,
            "noop": True,
        }

    now = utcnow()
    previous = await store.find_one(
        "model_versions", {"model_id": model_id, "status": "production"}
    )
    previous_version = None
    if previous and previous.get("_id") != target.get("_id"):
        previous_version = previous.get("version")
        await store.update_one(
            "model_versions",
            {"_id": previous["_id"]},
            {"$set": {"status": "deprecated", "deprecated_at": now}},
        )
    await store.update_one(
        "model_versions",
        {"_id": target["_id"]},
        {
            "$set": {
                "status": "production",
                "promoted_to_production_at": now,
                "deprecated_at": None,
            }
        },
    )
    await store.update_one(
        "models",
        {"_id": model_id},
        {"$set": {"production_version_id": target["_id"]}},
    )
    await create_audit_event(
        store,
        org_id=user["org_id"],
        project_id=model["project_id"],
        actor=audit_actor_for_user(user),
        event_type="model_version.promoted",
        resource_type="model_version",
        resource_id=target["_id"],
        diff={
            "before": {"version": previous_version, "status": "production"},
            "after": {"version": target.get("version"), "status": "production"},
        },
    )
    return {
        "model_id": model_id,
        "promoted_version": target.get("version"),
        "previous_version": previous_version,
        "noop": False,
    }


@router.get("/models/{model_id}/versions/compare")
async def compare_versions(
    model_id: str,
    a: str,
    b: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_same_org(await store.find_one("models", {"_id": model_id}), user)
    version_a = await store.find_one("model_versions", {"model_id": model_id, "version": a})
    version_b = await store.find_one("model_versions", {"model_id": model_id, "version": b})
    if not version_a or not version_b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or both versions were not found")
    model = await store.find_one("models", {"_id": model_id})
    positive_label = (model or {}).get("labels", {}).get("positive", "high_risk")

    async def summarize(version_name: str) -> dict:
        predictions = await store.find_many("predictions", {"model_id": model_id, "model_version": version_name}, limit=0)
        scores = [float(item.get("prediction", {}).get("score", 0)) for item in predictions]
        positives = sum(1 for item in predictions if item.get("prediction", {}).get("label") == positive_label)
        with_feedback = [item for item in predictions if item.get("feedback", {}).get("available")]
        cm = {key: 0 for key in ["tp", "fp", "tn", "fn"]}
        for item in with_feedback:
            result = item.get("feedback", {}).get("classification_result")
            if result in cm:
                cm[result] += 1
        return {
            "prediction_count": len(predictions),
            "positive_rate": round(positives / len(predictions), 4) if predictions else 0,
            "avg_score": round(sum(scores) / len(scores), 4) if scores else 0,
            "with_feedback": len(with_feedback),
            "confusion_matrix": cm,
        }

    summary_a = await summarize(a)
    summary_b = await summarize(b)
    return {
        "model_id": model_id,
        "version_a": {"metadata": version_a, "online_summary": summary_a},
        "version_b": {"metadata": version_b, "online_summary": summary_b},
        "delta": {
            "prediction_count": summary_b["prediction_count"] - summary_a["prediction_count"],
            "positive_rate": round(summary_b["positive_rate"] - summary_a["positive_rate"], 4),
            "avg_score": round(summary_b["avg_score"] - summary_a["avg_score"], 4),
        },
        "methodological_warning": "Comparacao sujeita a periodo, populacao e drift.",
    }


@router.get("/models/{model_id}/confusion-matrix")
async def confusion_matrix(
    model_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_same_org(await store.find_one("models", {"_id": model_id}), user)
    snapshots = await recompute_model_metrics(store, model_id)
    totals = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    for snapshot in snapshots:
        for key in totals:
            totals[key] += snapshot["confusion_matrix"][key]
    return {"model_id": model_id, "confusion_matrix": totals}


@router.get("/models/{model_id}/score-distribution")
async def score_distribution(
    model_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_same_org(await store.find_one("models", {"_id": model_id}), user)
    snapshots = await recompute_model_metrics(store, model_id)
    return {"items": [{"period": item["period"], "histogram": item["score_distribution"]["histogram"]} for item in snapshots]}


@router.post("/models/{model_id}/drift/run")
async def run_drift(
    model_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_same_org(await store.find_one("models", {"_id": model_id}), user)
    return await generate_drift_report(store, model_id)


@router.get("/models/{model_id}/drift")
async def list_drift_reports(
    model_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_same_org(await store.find_one("models", {"_id": model_id}), user)
    reports = await store.find_many("drift_reports", {"model_id": model_id}, sort=[("created_at", -1)], limit=20)
    return {"items": reports}


@router.get("/models/{model_id}/drift/heatmap")
async def drift_heatmap(
    model_id: str,
    limit: int = 12,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    """Pivota os ultimos N relatorios de drift em uma matriz feature x tempo.

    A celula contem o PSI da feature naquela rodada de drift. Quando o relatorio
    nao tem PSI por feature (relatorios antigos), o valor cai para o ``delta``
    absoluto como aproximacao. O frontend usa esse valor para colorir o heatmap.
    """
    require_same_org(await store.find_one("models", {"_id": model_id}), user)
    capped = max(1, min(int(limit or 12), 36))
    reports = await store.find_many(
        "drift_reports",
        {"model_id": model_id, "status": {"$ne": "insufficient_data"}},
        sort=[("created_at", -1)],
        limit=capped,
    )
    if not reports:
        return {"model_id": model_id, "buckets": [], "features": [], "thresholds": {"attention": 0.1, "drift": 0.25}}

    reports = list(reversed(reports))
    feature_set: dict[str, dict[str, Any]] = {}
    buckets: list[dict[str, Any]] = []
    for report in reports:
        bucket_id = report.get("created_at") or report.get("_id")
        bucket: dict[str, Any] = {
            "id": str(bucket_id),
            "created_at": report.get("created_at"),
            "model_version": report.get("model_version"),
            "score_psi": ((report.get("prediction_drift") or {}).get("psi", 0.0)),
            "score_status": ((report.get("prediction_drift") or {}).get("status", "stable")),
            "values": {},
        }
        rows = ((report.get("data_drift") or {}).get("features") or [])
        for row in rows:
            name = str(row.get("name", ""))
            if not name:
                continue
            psi = row.get("psi")
            value = float(psi) if isinstance(psi, (int, float)) else abs(float(row.get("delta") or 0.0))
            bucket["values"][name] = round(value, 4)
            feature_set.setdefault(
                name,
                {
                    "name": name,
                    "type": row.get("type", "continuous"),
                    "max_psi": 0.0,
                    "samples": 0,
                },
            )
            feature_set[name]["max_psi"] = max(feature_set[name]["max_psi"], value)
            feature_set[name]["samples"] += 1
        buckets.append(bucket)

    sorted_features = sorted(
        feature_set.values(), key=lambda item: (item["max_psi"], item["samples"]), reverse=True
    )
    return {
        "model_id": model_id,
        "buckets": buckets,
        "features": sorted_features,
        "thresholds": {"attention": 0.1, "drift": 0.25},
    }


@router.get("/models/{model_id}/bias-analysis")
async def bias_analysis(
    model_id: str,
    feature: str = "scholarship",
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    require_same_org(await store.find_one("models", {"_id": model_id}), user)
    model = await store.find_one("models", {"_id": model_id})
    positive_label = (model or {}).get("labels", {}).get("positive", "high_risk")
    predictions = await store.find_many("predictions", {"model_id": model_id}, limit=0)
    groups: dict[str, list[dict]] = {}
    for item in predictions:
        key = str((item.get("features") or {}).get(feature, "missing"))
        groups.setdefault(key, []).append(item)
    rows = []
    for group, items in groups.items():
        positives = sum(1 for item in items if item["prediction"]["label"] == positive_label)
        feedback = [item for item in items if item.get("feedback", {}).get("available")]
        tp = sum(1 for item in feedback if item["feedback"]["classification_result"] == "tp")
        fp = sum(1 for item in feedback if item["feedback"]["classification_result"] == "fp")
        fn = sum(1 for item in feedback if item["feedback"]["classification_result"] == "fn")
        precision = tp / (tp + fp) if tp + fp else None
        recall = tp / (tp + fn) if tp + fn else None
        rows.append(
            {
                "group": group,
                "total": len(items),
                "positive_rate": round(positives / len(items), 4) if items else 0,
                "precision": round(precision, 4) if precision is not None else None,
                "recall": round(recall, 4) if recall is not None else None,
            }
        )
    return {
        "model_id": model_id,
        "feature": feature,
        "rows": rows,
        "methodological_warning": "Diferencas entre grupos exigem validacao de dominio.",
    }
