from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from app.bot.handlers import router
from app.core.config import settings
from app.infra.redis import close_redis


def create_bot() -> Bot:
    return Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    return dispatcher


async def run_polling() -> None:
    """Запускает polling Telegram-бота и освобождает ресурсы при остановке."""
    bot = create_bot()
    dispatcher = create_dispatcher()
    try:
        await dispatcher.start_polling(bot)
    finally:
        await close_redis()
        await bot.session.close()