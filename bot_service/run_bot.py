import asyncio

from app.bot.dispatcher import run_polling


def main() -> None:
    asyncio.run(run_polling())


if __name__ == "__main__":
    main()