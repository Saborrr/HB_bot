from aiogram import Router

from aiogram.filters import CommandStart
from aiogram.types import Message

import app.keyboards as kb
import app.database.requests as rq


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Функция приветствия."""
    # Сохранение параметров пользователя в базу данных если его там нет
    await rq.set_user(message.from_user.id)
    text = (f'{message.from_user.full_name}, приветствуем Вас 😊\n')
    await message.answer(text=text,
                         reply_markup=await kb.inline_months())
