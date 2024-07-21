from aiogram import Router

from aiogram.filters import CommandStart
from aiogram.types import Message

import app.keyboards as kb


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Функция приветствия."""
    text = (f'{message.from_user.full_name}, приветствуем Вас 😊\n')
    await message.answer(text=text,
                         reply_markup=await kb.inline_months())
