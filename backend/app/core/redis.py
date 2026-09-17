"""Asynchronous Redis client lifecycle management."""

from redis.asyncio import Redis

from app.core.config import settings

redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


async def close_redis() -> None:
    """Close Redis connections when the application shuts down."""
    await redis_client.aclose()
