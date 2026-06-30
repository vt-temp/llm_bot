from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.core.jwt import TokenExpiredError, TokenValidationError, decode_and_validate
from app.infra.redis import get_redis
from app.tasks.llm_tasks import llm_request

router = Router()

TOKEN_HELP = "Отправьте токен командой /token &lt;jwt&gt;."


def token_key(telegram_user_id: int) -> str:
    """Строит Redis-ключ для хранения JWT конкретного пользователя Telegram."""
    return f"token:{telegram_user_id}"


@router.message(Command("start"))
async def start(message: Message) -> None:
    """Отправляет пользователю краткую инструкцию по началу работы с ботом."""
    await message.answer(
        "Бот запущен. Сначала авторизуйтесь через Auth Service, затем " + TOKEN_HELP
    )


@router.message(Command("token"))
async def save_token(message: Message) -> None:
    """Проверяет присланный JWT и сохраняет его в Redis для текущего пользователя."""
    token = message.text.removeprefix("/token").strip() if message.text else ""
    if not token:
        await message.answer("Передайте токен в формате /token &lt;jwt&gt;.")
        return

    try:
        decode_and_validate(token)
    except TokenExpiredError:
        await message.answer("Срок действия токена истек. Получите новый токен в Auth Service.")
        return
    except TokenValidationError:
        await message.answer("Токен некорректен. Проверьте его и попробуйте снова.")
        return

    redis = get_redis()
    await redis.set(token_key(message.from_user.id), token)
    await message.answer("Токен принят и сохранен.")


@router.message(F.text)
async def handle_prompt(message: Message) -> None:
    """Проверяет сохраненный JWT и ставит пользовательский запрос в очередь Celery."""
    if not message.text or message.text.startswith("/token") or message.text.startswith("/start"):
        return

    redis = get_redis()
    stored_token = await redis.get(token_key(message.from_user.id))
    if not stored_token:
        await message.answer(
            "Сначала авторизуйтесь через Auth Service и передайте токен. " + TOKEN_HELP
        )
        return

    try:
        decode_and_validate(stored_token)
    except TokenExpiredError:
        await redis.delete(token_key(message.from_user.id))
        await message.answer(
            "Срок действия токена истек. Получите новый токен и отправьте /token &lt;jwt&gt;."
        )
        return
    except TokenValidationError:
        await redis.delete(token_key(message.from_user.id))
        await message.answer("Сохраненный токен невалиден. Повторите авторизацию через Auth Service.")
        return

    llm_request.delay(message.chat.id, message.text)
    await message.answer("Запрос принят в обработку.")