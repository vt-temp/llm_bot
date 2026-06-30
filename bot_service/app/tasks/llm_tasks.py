import asyncio

from aiogram import Bot

from app.core.config import settings
from app.infra.celery_app import celery_app
from app.services.openrouter_client import OpenRouterError, call_openrouter


async def _send_message(chat_id: int, text: str) -> None:
    """Отправляет сообщение пользователю Telegram из фонового воркера."""
    bot = Bot(token=settings.bot_token)
    try:
        await bot.send_message(chat_id=chat_id, text=text)
    finally:
        await bot.session.close()


async def _process_request(chat_id: int, prompt: str) -> str:
    """Получает ответ от LLM и пересылает его пользователю в Telegram."""
    try:
        answer = await call_openrouter(prompt)
    except OpenRouterError as exc:
        answer = f"Не удалось получить ответ от LLM: {exc}"

    await _send_message(chat_id, answer)
    return answer


@celery_app.task(name="app.tasks.llm_tasks.llm_request")
def llm_request(tg_chat_id: int, prompt: str) -> str:
    """Точка входа Celery для асинхронной обработки пользовательского запроса."""
    return asyncio.run(_process_request(tg_chat_id, prompt))