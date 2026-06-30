from collections.abc import AsyncIterator

import fakeredis.aioredis
import pytest


@pytest.fixture
async def fake_redis() -> AsyncIterator[fakeredis.aioredis.FakeRedis]:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield redis
    await redis.flushall()
    await redis.aclose()


@pytest.fixture
def patch_handlers_redis(
    fake_redis: fakeredis.aioredis.FakeRedis,
    monkeypatch: pytest.MonkeyPatch,
) -> fakeredis.aioredis.FakeRedis:
    """Подменяет get_redis в обработчиках бота на fakeredis."""
    monkeypatch.setattr("app.bot.handlers.get_redis", lambda: fake_redis)
    return fake_redis