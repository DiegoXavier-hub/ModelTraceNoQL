from __future__ import annotations

from typing import Any

from app.core.privacy import redact_sensitive
from app.core.utils import make_id, utcnow
from app.db.document_store import DocumentStore


async def create_audit_event(
    store: DocumentStore,
    *,
    org_id: str,
    project_id: str | None,
    actor: dict[str, Any],
    event_type: str,
    resource_type: str,
    resource_id: str,
    diff: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = {
        "_id": make_id("audit"),
        "org_id": org_id,
        "project_id": project_id,
        "actor": redact_sensitive(actor),
        "event_type": event_type,
        "resource": {"type": resource_type, "id": resource_id},
        "diff": redact_sensitive(diff or {}),
        "context": redact_sensitive(context or {}),
        "created_at": utcnow(),
    }
    return await store.insert_one("audit_events", event)
