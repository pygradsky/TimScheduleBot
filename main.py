import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from src.utils.setup import setup
from src.db.db_operations import close_db
from src.handlers import __all_routers__
from src.handlers.schedule_cmd import build_cache


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
    build_cache()
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        logging.basicConfig(level=logging.INFO)
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        try:
            asyncio.run(close_db())
        except:
            pass
