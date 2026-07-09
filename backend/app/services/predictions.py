from __future__ import annotations

from fastapi import HTTPException, status

from app.core.privacy import (
    audit_actor_for_api_key,
    audit_actor_for_user,
    protect_display_name,
    protect_entity_id,
    redact_sensitive,
)
from app.core.utils import compute_classification_result, compute_score_band, make_id, utcnow
from app.db.document_store import DocumentStore
from app.schemas import FeedbackPayload, PredictionPayload
from app.services.audit import create_audit_event
from app.services.data_contracts import validate_prediction_contract
from app.services.metrics import recompute_model_metrics


async def record_prediction(
    store: DocumentStore,
    payload: PredictionPayload,
    actor_context: dict,
) -> dict:
    project = await store.find_one("projects", {"_id": payload.project_id, "status": "active"})
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if actor_context["org_id"] != project["org_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Project is not available for this credential")
    if actor_context["type"] == "api_key" and actor_context.get("project_id") != payload.project_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key cannot write to this project")

    model = await store.find_one("models", {"_id": payload.model_id, "project_id": payload.project_id, "status": "active"})
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    version = await store.find_one(
        "model_versions",
        {"model_id": payload.model_id, "version": payload.model_version},
    )
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model version not found")

    request_id = payload.metadata.get("request_id")
    if request_id:
        existing = await store.find_one("predictions", {"metadata.request_id": request_id})
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Duplicated request_id")

    score = float(payload.prediction["score"])
    threshold = float(payload.prediction.get("threshold", model.get("default_threshold", 0.5)))
    label = str(payload.prediction["label"])
    positive_label = model.get("labels", {}).get("positive", "high_risk")
    contract_report = validate_prediction_contract(project, model, payload.features)
    if contract_report["blocking"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Data contract violation", "contract": contract_report},
        )

    now = utcnow()
    prediction = {
        "_id": make_id("pred"),
        "project_id": payload.project_id,
        "org_id": project["org_id"],
        "model_id": payload.model_id,
        "model_version_id": version["_id"],
        "model_version": payload.model_version,
        "entity": {
            **protect_entity_id(payload.entity_id),
            "type": payload.entity_type,
            **protect_display_name(payload.entity_display_name),
        },
        "created_at": now,
        "features": payload.features,
        "prediction": {
            **payload.prediction,
            "label": label,
            "score": score,
            "threshold": threshold,
            "above_threshold": score >= threshold,
            "score_band": compute_score_band(score),
        },
        "explanations": payload.explanations,
        "decision": {
            "action": payload.decision.get("action", "no_action" if label != positive_label else "review"),
            "status": payload.decision.get("status", "not_triggered" if label != positive_label else "triggered"),
            "reason": payload.decision.get("reason", "score_above_threshold" if score >= threshold else "score_below_threshold"),
            "triggered_at": payload.decision.get("triggered_at", now if score >= threshold else None),
        },
        "feedback": {
            "available": False,
            "observed_label": None,
            "observed_value": None,
            "classification_result": None,
            "received_at": None,
            "source": None,
            "notes": None,
        },
        "annotations": [],
        "flags": {
            "is_critical": score >= 0.85 or label == positive_label,
            "reviewed_by": None,
            "reviewed_at": None,
            "contract_status": contract_report["status"],
        },
        "metadata": {
            **redact_sensitive(payload.metadata),
            "request_id": request_id,
            "contract": contract_report,
        },
    }

    await store.insert_one("predictions", prediction)
    await store.delete_many("dashboard_cache", {"project_id": payload.project_id})
    await store.delete_many("diagnostic_cache", {"model_id": payload.model_id})
    await store.update_one(
        "projects",
        {"_id": payload.project_id},
        {
            "$inc": {"stats.total_predictions": 1},
            "$set": {"stats.last_prediction_at": now},
        },
    )
    actor = (
        audit_actor_for_api_key(actor_context["api_key"])
        if actor_context["type"] == "api_key"
        else audit_actor_for_user(actor_context["user"])
    )
    await create_audit_event(
        store,
        org_id=project["org_id"],
        project_id=payload.project_id,
        actor=actor,
        event_type="prediction.recorded",
        resource_type="prediction",
        resource_id=prediction["_id"],
        context={"request_id": request_id},
    )
    return prediction


async def add_feedback(store: DocumentStore, prediction_id: str, payload: FeedbackPayload, actor_context: dict) -> dict:
    prediction = await store.find_one("predictions", {"_id": prediction_id})
    if not prediction or prediction["org_id"] != actor_context["org_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    if actor_context["type"] == "api_key" and actor_context.get("project_id") != prediction["project_id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key cannot write feedback to this project")

    model = await store.find_one("models", {"_id": prediction["model_id"]})
    positive_label = (model or {}).get("labels", {}).get("positive", "high_risk")
    negative_label = (model or {}).get("labels", {}).get("negative", "negative")
    predicted_positive = prediction["prediction"]["label"] == positive_label or bool(
        prediction["prediction"].get("above_threshold")
    )
    classification_result = None
    if payload.observed_value is not None:
        actual_positive = bool(payload.observed_value)
        classification_result = compute_classification_result(predicted_positive, actual_positive)
    elif payload.observed_label == positive_label:
        actual_positive = True
        classification_result = compute_classification_result(predicted_positive, actual_positive)
    elif payload.observed_label == negative_label:
        actual_positive = False
        classification_result = compute_classification_result(predicted_positive, actual_positive)
    else:
        actual_positive = None
        classification_result = "inconclusive"

    feedback = {
        "available": True,
        "observed_label": payload.observed_label,
        "observed_value": payload.observed_value,
        "classification_result": classification_result,
        "received_at": utcnow(),
        "feedback_date": payload.feedback_date,
        "source": payload.source,
        "notes": payload.notes,
    }
    await store.update_one("predictions", {"_id": prediction_id}, {"$set": {"feedback": feedback}})
    await store.delete_many("dashboard_cache", {"project_id": prediction["project_id"]})
    await store.delete_many("diagnostic_cache", {"model_id": prediction["model_id"]})
    audit_actor = (
        audit_actor_for_api_key(actor_context["api_key"])
        if actor_context["type"] == "api_key"
        else audit_actor_for_user(actor_context["user"])
    )
    await create_audit_event(
        store,
        org_id=prediction["org_id"],
        project_id=prediction["project_id"],
        actor=audit_actor,
        event_type="prediction.feedback_added",
        resource_type="prediction",
        resource_id=prediction_id,
        diff={"after": {"feedback": feedback}},
    )
    await recompute_model_metrics(store, prediction["model_id"])
    updated = await store.find_one("predictions", {"_id": prediction_id})
    return updated or prediction
