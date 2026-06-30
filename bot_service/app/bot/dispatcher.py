from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from app.bot.handlers import router
from app.core.config import settings


def create_bot() -> Bot:
    return Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))


def create_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    return dispatcher


async def run_polling() -> None:
    bot = create_bot()
    dispatcher = create_dispatcher()
    await dispatcher.start_polling(bot)