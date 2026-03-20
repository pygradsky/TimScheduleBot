import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from src.utils.setup import setup
from src.bot.handlers import __all_routers__


async def main() -> None:
    load_dotenv()

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set in the environment or .env file.")

    bot = Bot(token=token)
    dp = Dispatcher()

    for router in __all_routers__:
        dp.include_router(router)

    await setup()
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        logging.basicConfig(level=logging.INFO)
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
