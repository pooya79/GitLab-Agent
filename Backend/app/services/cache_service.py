import datetime as dt
from typing import Optional
from sqlalchemy import select, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Cache


def NOW():
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


class CacheService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, key: str) -> Optional[str]:
        result = await self.session.execute(
            select(Cache).where(
                Cache.key == key,
                or_(Cache.expires_at is None, Cache.expires_at > NOW()),
            )
        )
        cache_entry = result.scalar_one_or_none()
        if cache_entry:
            return cache_entry.value
        return None

    async def set(self, key: str, value: str, ttl_seconds: Optional[int] = None):
        expires_at = NOW() + dt.timedelta(seconds=ttl_seconds) if ttl_seconds else None

        # Delete existing cache entry if it exists
        await self.session.execute(delete(Cache).where(Cache.key == key))

        new_cache_entry = Cache(key=key, value=value, expires_at=expires_at)
        self.session.add(new_cache_entry)
        await self.session.commit()

    async def delete(self, key: str):
        await self.session.execute(delete(Cache).where(Cache.key == key))
        await self.session.commit()

    async def clear_expired(self):
        await self.session.execute(
            delete(Cache).where(
                (Cache.expires_at is not None) & (Cache.expires_at <= NOW())
            )
        )
        await self.session.commit()
