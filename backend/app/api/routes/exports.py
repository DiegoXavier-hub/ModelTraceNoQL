from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.api.dependencies import get_current_user, get_store
from app.core.config import settings
from app.core.privacy import (
    audit_actor_for_user,
    blind_index,
    redact_prediction_for_export,
    redact_sensitive,
    reveal_entity,
    reveal_predictions_for_user,
)
from app.core.utils import make_id, utcnow
from app.db.document_store import DocumentStore
from app.schemas import ExportPayload
from app.services.audit import create_audit_event

router = APIRouter(tags=["exports"])


def _export_dir() -> Path:
    path = Path(settings.local_store_path).resolve().parent / "exports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _normalize_filters(filters: dict[str, Any], org_id: str) -> dict[str, Any]:
    normalized = {"org_id": org_id}
    allowed = {
        "project_id": "project_id",
        "model_id": "model_id",
        "model_version": "model_version",
        "label": "prediction.label",
        "score_band": "prediction.score_band",
        "feedback_available": "feedback.available",
    }
    for source, target in allowed.items():
        if source in filters and filters[source] is not None:
            normalized[target] = filters[source]
    return normalized


def _flatten_prediction(
    item: dict[str, Any],
    include_features: bool,
    include_explanations: bool,
    redact_pii: bool,
) -> dict[str, Any]:
    entity = item.get("entity", {}) if redact_pii else reveal_entity(item.get("entity", {}))
    raw_entity_id = entity.get("id")
    raw_request_id = item.get("metadata", {}).get("request_id")
    row = {
        "prediction_id": item["_id"],
        "project_id": item["project_id"],
        "model_id": item["model_id"],
        "model_version": item.get("model_version"),
        "entity_id": entity.get("id_hash") or blind_index(str(raw_entity_id), "entity") if redact_pii and raw_entity_id else raw_entity_id,
        "entity_type": entity.get("type"),
        "created_at": item.get("created_at"),
        "label": item.get("prediction", {}).get("label"),
        "score": item.get("prediction", {}).get("score"),
        "threshold": item.get("prediction", {}).get("threshold"),
        "score_band": item.get("prediction", {}).get("score_band"),
        "feedback_available": item.get("feedback", {}).get("available"),
        "classification_result": item.get("feedback", {}).get("classification_result"),
        "decision_action": item.get("decision", {}).get("action"),
        "request_id": blind_index(str(raw_request_id), "request_id") if redact_pii and raw_request_id else raw_request_id,
    }
    if include_features:
        features = redact_sensitive(item.get("features", {})) if redact_pii else item.get("features", {})
        row["features"] = json.dumps(features, ensure_ascii=False)
    if include_explanations:
        explanations = redact_sensitive(item.get("explanations", [])) if redact_pii else item.get("explanations", [])
        row["explanations"] = json.dumps(explanations, ensure_ascii=False)
    return row


@router.post("/exports", status_code=201)
async def create_export(
    payload: ExportPayload,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    filter_ = _normalize_filters(payload.filters, user["org_id"])
    items = await store.find_many("predictions", filter_, sort=[("created_at", -1)], limit=0)
    export_id = make_id("export")
    suffix = payload.format
    file_path = _export_dir() / f"{export_id}.{suffix}"

    if payload.format == "json":
        export_items = [redact_prediction_for_export(item) for item in items] if payload.redact_pii else reveal_predictions_for_user(items)
        file_path.write_text(json.dumps(export_items, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        rows = [
            _flatten_prediction(item, payload.include_features, payload.include_explanations, payload.redact_pii)
            for item in items
        ]
        fieldnames = list(rows[0].keys()) if rows else ["prediction_id"]
        with file_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    doc = {
        "_id": export_id,
        "org_id": user["org_id"],
        "project_id": payload.filters.get("project_id"),
        "type": payload.type,
        "filters": payload.filters,
        "format": payload.format,
        "include_features": payload.include_features,
        "include_explanations": payload.include_explanations,
        "redact_pii": payload.redact_pii,
        "status": "ready",
        "file_path": str(file_path),
        "record_count": len(items),
        "created_by": user["_id"],
        "created_at": utcnow(),
    }
    await store.insert_one("exports", doc)
    await create_audit_event(
        store,
        org_id=user["org_id"],
        project_id=doc["project_id"],
        actor=audit_actor_for_user(user),
        event_type="export.created",
        resource_type="export",
        resource_id=export_id,
        diff={"after": {key: value for key, value in doc.items() if key != "file_path"}},
    )
    return {key: value for key, value in doc.items() if key != "file_path"}


@router.get("/exports")
async def list_exports(
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    exports = await store.find_many("exports", {"org_id": user["org_id"]}, sort=[("created_at", -1)], limit=100)
    return {"items": [{key: value for key, value in item.items() if key != "file_path"} for item in exports]}


@router.get("/exports/{export_id}")
async def get_export(
    export_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict:
    export = await store.find_one("exports", {"_id": export_id, "org_id": user["org_id"]})
    if not export:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")
    return {key: value for key, value in export.items() if key != "file_path"}


@router.get("/exports/{export_id}/download")
async def download_export(
    export_id: str,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> FileResponse:
    export = await store.find_one("exports", {"_id": export_id, "org_id": user["org_id"]})
    if not export:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")
    file_path = Path(export["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export file not found")
    media_type = "text/csv" if export["format"] == "csv" else "application/json"
    return FileResponse(file_path, media_type=media_type, filename=file_path.name)
