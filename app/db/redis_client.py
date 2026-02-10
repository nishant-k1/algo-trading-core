"""Redis connection (cache, session)."""

import redis
import redis.asyncio as redis_async

from app.config import settings

_redis: redis_async.Redis | None = None
_redis_sync: redis.Redis | None = None


def get_redis_sync() -> redis.Redis:
    """Sync Redis client for cache (e.g. market data)."""
    global _redis_sync
    if _redis_sync is None:
        _redis_sync = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=False,
        )
    return _redis_sync


async def get_redis() -> redis_async.Redis:
    """Get or create async Redis client."""
    global _redis
    if _redis is None:
        _redis = redis_async.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis


async def close_redis() -> None:
    """Close Redis connection (e.g. on shutdown)."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def close_redis_sync() -> None:
    """Close sync Redis connection."""
    global _redis_sync
    if _redis_sync is not None:
        _redis_sync.close()
        _redis_sync = None
