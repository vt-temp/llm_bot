from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from jose import jwt

from app.bot.handlers import handle_prompt, save_token, token_key
from app.core.config import settings


def make_message(text: str, user_id: int = 101, chat_id: int = 202) -> SimpleNamespace:
    return SimpleNamespace(
        text=text,
        from_user=SimpleNamespace(id=user_id),
        chat=SimpleNamespace(id=chat_id),
        answer=AsyncMock(),
    )


def make_token() -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": "1",
        "role": "user",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


@pytest.mark.asyncio
async def test_save_token_persists_value(patch_handlers_redis) -> None:
    message = make_message(f"/token {make_token()}")

    await save_token(message)

    assert await patch_handlers_redis.get(token_key(101)) is not None
    message.answer.assert_awaited_once_with("Токен принят и сохранен.")


@pytest.mark.asyncio
async def test_handle_prompt_rejects_missing_token(patch_handlers_redis, monkeypatch: pytest.MonkeyPatch) -> None:
    delay_mock = Mock()
    monkeypatch.setattr("app.bot.handlers.llm_request", SimpleNamespace(delay=delay_mock))
    message = make_message("Привет")

    await handle_prompt(message)

    delay_mock.assert_not_called()
    message.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_prompt_enqueues_task_for_valid_token(
    patch_handlers_redis,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    delay_mock = Mock()
    monkeypatch.setattr("app.bot.handlers.llm_request", SimpleNamespace(delay=delay_mock))
    await patch_handlers_redis.set(token_key(101), make_token())
    message = make_message("Объясни JWT")

    await handle_prompt(message)

    delay_mock.assert_called_once_with(202, "Объясни JWT")
    message.answer.assert_awaited_once_with("Запрос принят в обработку.")