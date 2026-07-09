from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_store
from app.core.privacy import reveal_entity
from app.db.document_store import DocumentStore

router = APIRouter(tags=["usage"])

# Custos estimados em BRL por unidade. Valores ilustrativos.
# Em producao real, viria de tabela de pricing por org/plano.
COST_PER_PREDICTION_BRL = 0.0009
COST_PER_API_CALL_BRL = 0.0003
COST_PER_GB_STORAGE_BRL = 0.45
AVG_PREDICTION_BYTES = 1800  # JSON medio incluindo features + decision + metadata


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _bucket_label(date: datetime) -> str:
    return date.strftime("%Y-%m-%d")


@router.get("/usage/summary")
async def usage_summary(
    days: int = 30,
    user: dict = Depends(get_current_user),
    store: DocumentStore = Depends(get_store),
) -> dict[str, Any]:
    """Resumo de consumo por organizacao.

    Agrega quantidade de predicoes, eventos de auditoria, chaves de API ativas e
    armazenamento estimado, alem de serie diaria dos ultimos ``days`` dias e top
    entidades por volume. Custos sao estimados via constantes pricing.
    """
    capped_days = max(7, min(int(days or 30), 90))
    org_id = user["org_id"]
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=capped_days)

    predictions = await store.find_many("predictions", {"org_id": org_id}, limit=0)
    audit_events = await store.find_many("audit_events", {"org_id": org_id}, limit=0)
    api_keys = await store.find_many("api_keys", {"org_id": org_id}, limit=0)
    projects = await store.find_many("projects", {"org_id": org_id}, limit=0)
    models = await store.find_many("models", {"org_id": org_id}, limit=0)

    predictions_total = len(predictions)
    audit_events_total = len(audit_events)
    api_keys_active = sum(1 for key in api_keys if not key.get("revoked_at"))
    api_keys_total = len(api_keys)

    storage_bytes = predictions_total * AVG_PREDICTION_BYTES
    storage_gb = storage_bytes / (1024 ** 3)

    # Serie diaria + top entidades
    daily: dict[str, dict[str, int]] = {}
    entity_volume: dict[str, int] = {}
    feedback_recent = 0

    for prediction in predictions:
        created = _parse_timestamp(prediction.get("created_at"))
        if not created or created < cutoff:
            continue
        bucket = _bucket_label(created)
        bucket_data = daily.setdefault(bucket, {"predictions": 0, "feedback": 0, "with_feedback": 0})
        bucket_data["predictions"] += 1
        if (prediction.get("feedback") or {}).get("available"):
            bucket_data["with_feedback"] += 1
            feedback_recent += 1
        # Sempre passar pela camada de privacidade: ela decifra ``id_encrypted``
        # e ``display_name_encrypted`` para usuarios autenticados, e retorna
        # apenas ``id_masked`` quando nao ha chave de descriptografia disponivel.
        revealed = reveal_entity(prediction.get("entity"))
        entity_label = (
            revealed.get("display_name")
            or revealed.get("id")
            or revealed.get("id_masked")
            or "—"
        )
        entity_label = str(entity_label).strip() or "—"
        if entity_label == "[protected]":
            entity_label = "—"
        entity_volume[entity_label] = entity_volume.get(entity_label, 0) + 1

    # Auditoria recente
    audit_recent = 0
    for event in audit_events:
        created = _parse_timestamp(event.get("created_at"))
        if not created or created < cutoff:
            continue
        audit_recent += 1

    series = []
    cursor = cutoff
    while cursor.date() <= now.date():
        bucket = _bucket_label(cursor)
        values = daily.get(bucket, {"predictions": 0, "feedback": 0, "with_feedback": 0})
        series.append(
            {
                "date": bucket,
                "predictions": values.get("predictions", 0),
                "with_feedback": values.get("with_feedback", 0),
            }
        )
        cursor += timedelta(days=1)

    top_entities = sorted(
        ({"entity": key, "predictions": value} for key, value in entity_volume.items()),
        key=lambda item: item["predictions"],
        reverse=True,
    )[:10]

    predictions_recent = sum(item["predictions"] for item in series)

    cost_predictions = predictions_recent * COST_PER_PREDICTION_BRL
    cost_audit = audit_recent * COST_PER_API_CALL_BRL
    cost_storage = storage_gb * COST_PER_GB_STORAGE_BRL
    cost_total = round(cost_predictions + cost_audit + cost_storage, 2)

    return {
        "period_days": capped_days,
        "generated_at": now.isoformat(),
        "totals": {
            "predictions_total": predictions_total,
            "predictions_recent": predictions_recent,
            "audit_events_total": audit_events_total,
            "audit_events_recent": audit_recent,
            "feedback_recent": feedback_recent,
            "api_keys_total": api_keys_total,
            "api_keys_active": api_keys_active,
            "projects": len(projects),
            "models": len(models),
            "storage_bytes": storage_bytes,
            "storage_gb": round(storage_gb, 4),
        },
        "series": series,
        "top_entities": top_entities,
        "cost_estimate_brl": {
            "predictions": round(cost_predictions, 2),
            "audit_events": round(cost_audit, 2),
            "storage": round(cost_storage, 2),
            "total": cost_total,
        },
        "pricing": {
            "currency": "BRL",
            "per_prediction": COST_PER_PREDICTION_BRL,
            "per_api_call": COST_PER_API_CALL_BRL,
            "per_gb_storage": COST_PER_GB_STORAGE_BRL,
        },
        "methodological_warning": "Estimativas de custo sao ilustrativas. Substitua por pricing real do provedor.",
    }
