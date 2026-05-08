"""
Redis Connection Management
"""
import redis.asyncio as aioredis
from typing import Optional
from .config import settings

_redis_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """
    Get Redis connection.
    """
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
            password=settings.REDIS_PASSWORD,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_pool


async def close_redis():
    """
    Close Redis connection.
    """
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None


class RedisClient:
    """
    Synchronous Redis client wrapper.
    """

    def __init__(self):
        import redis

        self._client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DB,
            decode_responses=True,
        )

    def get(self, key: str) -> Optional[str]:
        return self._client.get(key)

    def set(
        self, key: str, value: str, ex: Optional[int] = None
    ) -> bool:
        return self._client.set(key, value, ex=ex)

    def delete(self, key: str) -> int:
        return self._client.delete(key)

    def exists(self, key: str) -> bool:
        return self._client.exists(key) > 0

    def incr(self, key: str) -> int:
        return self._client.incr(key)

    def expire(self, key: str, seconds: int) -> bool:
        return self._client.expire(key, seconds)

    def setex(self, key: str, seconds: int, value: str) -> bool:
        return self._client.setex(key, seconds, value)


redis_client = RedisClient()