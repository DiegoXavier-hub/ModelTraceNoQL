from __future__ import annotations

from typing import Any

from app.core.utils import make_id, utcnow
from app.db.document_store import DocumentStore


async def create_notification(
    store: DocumentStore,
    *,
    org_id: str,
    user_id: str | None = None,
    project_id: str | None = None,
    type_: str,
    title: str,
    message: str,
    severity: str = "info",
    link: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    notification = {
        "_id": make_id("notif"),
        "org_id": org_id,
        "user_id": user_id,
        "project_id": project_id,
        "type": type_,
        "title": title,
        "message": message,
        "severity": severity,
        "link": link or {},
        "metadata": metadata or {},
        "read_at": None,
        "created_at": utcnow(),
    }
    await store.insert_one("notifications", notification)
    return notification
