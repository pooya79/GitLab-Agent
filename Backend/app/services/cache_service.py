import datetime as dt
from typing import Optional

from pymongo.collection import Collection
from pymongo.database import Database

from app.core.time import ensure_utc, utc_now


class CacheService:
    def __init__(self, db: Database):
        self.collection: Collection = db["cache"]

    def get(self, key: str) -> Optional[str]:
        cache_entry = self.collection.find_one({"key": key})
        if not cache_entry:
            return None

        expires_at = ensure_utc(cache_entry.get("expires_at"))
        if expires_at and expires_at <= utc_now():
            self.collection.delete_one({"_id": cache_entry["_id"]})
            return None
        return cache_entry.get("value")

    def set(self, key: str, value: str, ttl_seconds: Optional[int] = None) -> None:
        expires_at = (
            utc_now() + dt.timedelta(seconds=ttl_seconds) if ttl_seconds else None
        )
        set_doc: dict[str, object] = {"key": key, "value": value}
        update_ops: dict[str, dict[str, object]] = {"$set": set_doc}
        if expires_at:
            set_doc["expires_at"] = expires_at
        else:
            update_ops["$unset"] = {"expires_at": ""}

        self.collection.update_one({"key": key}, update_ops, upsert=True)

    def delete(self, key: str) -> None:
        self.collection.delete_one({"key": key})
