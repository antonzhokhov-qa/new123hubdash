"""Redis connection management."""

from typing import Optional
import redis.asyncio as redis
from app.config import settings

# Global Redis connection
_redis_client: Optional[redis.Redis] = None


async def init_redis() -> None:
    """Initialize Redis connection."""
    global _redis_client
    _redis_client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
    )
    # Verify connection
    await _redis_client.ping()


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


def get_redis() -> redis.Redis:
    """Get Redis client."""
    if _redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _redis_client


class RedisCache:
    """Redis cache helper."""

    def __init__(self):
        pass

    @property
    def client(self) -> redis.Redis:
        return get_redis()

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        return await self.client.get(key)

    async def set(self, key: str, value: str, ttl: int = 60) -> None:
        """Set value in cache with TTL."""
        await self.client.setex(key, ttl, value)

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        await self.client.delete(key)

    async def publish(self, channel: str, message: str) -> None:
        """Publish message to channel (for WebSocket notifications)."""
        await self.client.publish(channel, message)


cache = RedisCache()
