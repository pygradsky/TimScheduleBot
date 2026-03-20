from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram import Router

from src.bot.resources.messages import bot_messages

router = Router()


@router.message(CommandStart())
async def handle_start(message: Message) -> None:
    await message.answer(
        bot_messages['/start']
    )
