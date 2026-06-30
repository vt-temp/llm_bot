from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import settings


@lru_cache
def get_redis() -> Redis:
    """Возвращает общий Redis-клиент для Bot Service."""
    return Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)


async def close_redis() -> None:
    """Корректно закрывает общий Redis-клиент при остановке приложения."""
    redis = get_redis()
    await redis.aclose()
    get_redis.cache_clear()