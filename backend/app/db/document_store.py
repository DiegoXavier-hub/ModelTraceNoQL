from __future__ import annotations

import asyncio
import copy
import json
from pathlib import Path
from typing import Any, Callable

from app.core.config import Settings
from app.core.utils import get_nested, set_nested


COLLECTIONS = [
    "users",
    "organizations",
    "projects",
    "models",
    "model_versions",
    "api_keys",
    "email_tokens",
    "notifications",
    "jobs",
    "saved_views",
    "entity_notes",
    "prediction_scenarios",
    "predictions",
    "prediction_annotations",
    "prediction_replays",
    "metrics_snapshots",
    "dashboard_cache",
    "diagnostic_cache",
    "drift_reports",
    "alert_rules",
    "alerts",
    "webhooks",
    "webhook_deliveries",
    "datasets",
    "cohorts",
    "model_evaluations",
    "model_cards",
    "intervention_cases",
    "incidents",
    "data_quality_reports",
    "approvals",
    "audit_events",
    "exports",
]


class DocumentStore:
    async def connect(self) -> None:
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError

    async def ensure_indexes(self) -> None:
        raise NotImplementedError

    async def insert_one(self, collection: str, document: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def find_one(self, collection: str, filter_: dict[str, Any]) -> dict[str, Any] | None:
        raise NotImplementedError

    async def find_many(
        self,
        collection: str,
        filter_: dict[str, Any] | None = None,
        sort: list[tuple[str, int]] | None = None,
        limit: int = 100,
        skip: int = 0,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    async def count(self, collection: str, filter_: dict[str, Any] | None = None) -> int:
        raise NotImplementedError

    async def update_one(self, collection: str, filter_: dict[str, Any], update: dict[str, Any]) -> bool:
        raise NotImplementedError

    async def upsert_one(self, collection: str, filter_: dict[str, Any], document: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def delete_one(self, collection: str, filter_: dict[str, Any]) -> bool:
        raise NotImplementedError

    async def delete_many(self, collection: str, filter_: dict[str, Any]) -> int:
        raise NotImplementedError

    async def transform_many(
        self,
        collection: str,
        filter_: dict[str, Any],
        transform: Callable[[dict[str, Any]], dict[str, Any] | None],
    ) -> int:
        raise NotImplementedError


class JsonDocumentStore(DocumentStore):
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self._lock = asyncio.Lock()
        self._data: dict[str, list[dict[str, Any]]] = {name: [] for name in COLLECTIONS}

    async def connect(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._data = {name: list(raw.get(name, [])) for name in COLLECTIONS}
        else:
            await self._save()

    async def close(self) -> None:
        await self._save()

    async def ensure_indexes(self) -> None:
        return None

    async def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _matches(self, document: dict[str, Any], filter_: dict[str, Any] | None) -> bool:
        if not filter_:
            return True
        for key, expected in filter_.items():
            actual = get_nested(document, key)
            if isinstance(expected, dict):
                for op, value in expected.items():
                    if op == "$gte" and not (actual is not None and actual >= value):
                        return False
                    if op == "$lte" and not (actual is not None and actual <= value):
                        return False
                    if op == "$gt" and not (actual is not None and actual > value):
                        return False
                    if op == "$lt" and not (actual is not None and actual < value):
                        return False
                    if op == "$ne" and actual == value:
                        return False
                    if op == "$in" and actual not in value:
                        return False
                    if op == "$exists" and ((actual is not None) != bool(value)):
                        return False
            elif actual != expected:
                return False
        return True

    async def insert_one(self, collection: str, document: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            doc = copy.deepcopy(document)
            self._data[collection].append(doc)
            await self._save()
            return copy.deepcopy(doc)

    async def find_one(self, collection: str, filter_: dict[str, Any]) -> dict[str, Any] | None:
        async with self._lock:
            for document in self._data[collection]:
                if self._matches(document, filter_):
                    return copy.deepcopy(document)
        return None

    async def find_many(
        self,
        collection: str,
        filter_: dict[str, Any] | None = None,
        sort: list[tuple[str, int]] | None = None,
        limit: int = 100,
        skip: int = 0,
    ) -> list[dict[str, Any]]:
        async with self._lock:
            results = [doc for doc in self._data[collection] if self._matches(doc, filter_)]
        if sort:
            for field, direction in reversed(sort):
                results.sort(key=lambda item: get_nested(item, field), reverse=direction < 0)
        if skip:
            results = results[skip:]
        if limit:
            results = results[:limit]
        # Deep-copying every result was costing ~2s for 25k predictions and dominated
        # dashboard cold loads. The Mongo path returns plain dicts that the caller can
        # mutate freely; here we return references to the same dicts. All current
        # callers either serialize to JSON immediately or wrap with reveal_*_for_user
        # (which does its own deepcopy). Mutations to persisted state must go through
        # update_one / upsert_one, never by mutating a returned doc.
        return results

    async def count(self, collection: str, filter_: dict[str, Any] | None = None) -> int:
        async with self._lock:
            return sum(1 for doc in self._data[collection] if self._matches(doc, filter_))

    async def update_one(self, collection: str, filter_: dict[str, Any], update: dict[str, Any]) -> bool:
        async with self._lock:
            for document in self._data[collection]:
                if not self._matches(document, filter_):
                    continue
                if "$set" in update or "$inc" in update:
                    for path, value in update.get("$set", {}).items():
                        set_nested(document, path, value)
                    for path, value in update.get("$inc", {}).items():
                        current = get_nested(document, path, 0) or 0
                        set_nested(document, path, current + value)
                else:
                    document.clear()
                    document.update(copy.deepcopy(update))
                await self._save()
                return True
        return False

    async def upsert_one(self, collection: str, filter_: dict[str, Any], document: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            for index, existing in enumerate(self._data[collection]):
                if self._matches(existing, filter_):
                    self._data[collection][index] = copy.deepcopy(document)
                    await self._save()
                    return copy.deepcopy(document)
            self._data[collection].append(copy.deepcopy(document))
            await self._save()
            return copy.deepcopy(document)

    async def delete_one(self, collection: str, filter_: dict[str, Any]) -> bool:
        deleted = await self.delete_many(collection, filter_)
        return deleted > 0

    async def delete_many(self, collection: str, filter_: dict[str, Any]) -> int:
        async with self._lock:
            before = len(self._data[collection])
            self._data[collection] = [doc for doc in self._data[collection] if not self._matches(doc, filter_)]
            deleted = before - len(self._data[collection])
            if deleted:
                await self._save()
            return deleted

    async def transform_many(
        self,
        collection: str,
        filter_: dict[str, Any],
        transform: Callable[[dict[str, Any]], dict[str, Any] | None],
    ) -> int:
        async with self._lock:
            changed = 0
            for document in self._data[collection]:
                if not self._matches(document, filter_):
                    continue
                update = transform(document)
                if not update:
                    continue
                if "$set" in update:
                    for path, value in update["$set"].items():
                        set_nested(document, path, value)
                else:
                    document.clear()
                    document.update(copy.deepcopy(update))
                changed += 1
            if changed:
                await self._save()
            return changed


class MongoDocumentStore(DocumentStore):
    def __init__(self, url: str, db_name: str) -> None:
        self.url = url
        self.db_name = db_name
        self.client: Any = None
        self.db: Any = None

    async def connect(self) -> None:
        from motor.motor_asyncio import AsyncIOMotorClient

        self.client = AsyncIOMotorClient(self.url)
        self.db = self.client[self.db_name]
        await self.db.command("ping")

    async def close(self) -> None:
        if self.client:
            self.client.close()

    async def ensure_indexes(self) -> None:
        await self.db.users.create_index([("org_id", 1), ("email_hash", 1)], unique=True, sparse=True)
        await self.db.email_tokens.create_index([("token_hash", 1), ("purpose", 1)], unique=True)
        await self.db.email_tokens.create_index([("user_id", 1), ("purpose", 1), ("created_at", -1)])
        await self.db.notifications.create_index([("org_id", 1), ("user_id", 1), ("read_at", 1), ("created_at", -1)])
        await self.db.jobs.create_index([("org_id", 1), ("project_id", 1), ("created_at", -1)])
        await self.db.saved_views.create_index([("org_id", 1), ("user_id", 1), ("view", 1), ("created_at", -1)])
        await self.db.entity_notes.create_index([("org_id", 1), ("project_id", 1), ("entity_hash", 1), ("created_at", -1)])
        await self.db.prediction_scenarios.create_index([("org_id", 1), ("prediction_id", 1), ("created_at", -1)])
        await self.db.api_keys.create_index([("key_hash", 1)], unique=True, sparse=True)
        await self.db.predictions.create_index([("org_id", 1), ("project_id", 1), ("created_at", -1)])
        await self.db.predictions.create_index([("model_id", 1), ("model_version", 1), ("created_at", -1)])
        await self.db.predictions.create_index([("entity.id", 1), ("project_id", 1), ("created_at", -1)])
        await self.db.predictions.create_index([("entity.id_hash", 1), ("project_id", 1), ("created_at", -1)])
        await self.db.predictions.create_index([("prediction.score", -1), ("project_id", 1)])
        await self.db.predictions.create_index([("prediction.label", 1), ("model_id", 1)])
        await self.db.predictions.create_index([("prediction.score_band", 1), ("project_id", 1)])
        await self.db.predictions.create_index([("feedback.available", 1), ("model_id", 1)])
        await self.db.predictions.create_index([("feedback.classification_result", 1), ("model_id", 1)])
        await self.db.predictions.create_index([("metadata.request_id", 1)], unique=True, sparse=True)
        await self.db.dashboard_cache.create_index([("project_id", 1)], unique=True)
        await self.db.diagnostic_cache.create_index([("model_id", 1), ("slice_feature", 1)], unique=True)
        await self.db.prediction_replays.create_index([("prediction_id", 1), ("created_at", -1)])
        await self.db.metrics_snapshots.create_index(
            [("model_id", 1), ("period.granularity", 1), ("period.start", -1)]
        )
        await self.db.audit_events.create_index([("project_id", 1), ("created_at", -1)])
        await self.db.audit_events.create_index([("actor.id", 1), ("created_at", -1)])
        await self.db.audit_events.create_index([("event_type", 1), ("created_at", -1)])
        await self.db.alerts.create_index([("project_id", 1), ("status", 1), ("severity", 1), ("created_at", -1)])
        await self.db.intervention_cases.create_index([("project_id", 1), ("status", 1), ("priority", 1)])
        await self.db.model_evaluations.create_index([("project_id", 1), ("model_id", 1), ("window", 1)])
        await self.db.model_cards.create_index([("project_id", 1), ("model_id", 1)])
        await self.db.data_quality_reports.create_index([("project_id", 1), ("created_at", -1)])
        await self.db.cohorts.create_index([("project_id", 1), ("created_at", -1)])

    async def insert_one(self, collection: str, document: dict[str, Any]) -> dict[str, Any]:
        await self.db[collection].insert_one(copy.deepcopy(document))
        return copy.deepcopy(document)

    async def find_one(self, collection: str, filter_: dict[str, Any]) -> dict[str, Any] | None:
        return await self.db[collection].find_one(filter_, {"_id": 0})

    async def find_many(
        self,
        collection: str,
        filter_: dict[str, Any] | None = None,
        sort: list[tuple[str, int]] | None = None,
        limit: int = 100,
        skip: int = 0,
    ) -> list[dict[str, Any]]:
        cursor = self.db[collection].find(filter_ or {}, {"_id": 0})
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return await cursor.to_list(length=limit or None)

    async def count(self, collectmasion: str, filter_: dict[str, Any] | None = None) -> int:
        return await self.db[collection].count_documents(filter_ or {})

    async def update_one(self, collection: str, filter_: dict[str, Any], update: dict[str, Any]) -> bool:
        result = await self.db[collection].update_one(filter_, update)
        return result.modified_count > 0

    async def upsert_one(self, collection: str, filter_: dict[str, Any], document: dict[str, Any]) -> dict[str, Any]:
        await self.db[collection].replace_one(filter_, copy.deepcopy(document), upsert=True)
        return copy.deepcopy(document)

    async def delete_one(self, collection: str, filter_: dict[str, Any]) -> bool:
        result = await self.db[collection].delete_one(filter_)
        return result.deleted_count > 0

    async def delete_many(self, collection: str, filter_: dict[str, Any]) -> int:
        result = await self.db[collection].delete_many(filter_)
        return int(result.deleted_count)

    async def transform_many(
        self,
        collection: str,
        filter_: dict[str, Any],
        transform: Callable[[dict[str, Any]], dict[str, Any] | None],
    ) -> int:
        from pymongo import UpdateOne

        cursor = self.db[collection].find(filter_ or {})
        operations = []
        async for document in cursor:
            update = transform(document)
            if update:
                operations.append(UpdateOne({"_id": document["_id"]}, update))
        if not operations:
            return 0
        result = await self.db[collection].bulk_write(operations, ordered=False)
        return int(result.modified_count)


async def create_store(settings: Settings) -> DocumentStore:
    if settings.mongodb_url:
        store: DocumentStore = MongoDocumentStore(settings.mongodb_url, settings.mongodb_db_name)
    else:
        store = JsonDocumentStore(settings.local_store_path)
    await store.connect()
    await store.ensure_indexes()
    return store
