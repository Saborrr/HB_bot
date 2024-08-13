from aiogram import F, Router

from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

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


@router.message(F.text == 'Каталог')
async def catalog(message: Message):
    await message.answer('Выберите категорию товара',
                         reply_markup=await kb.categories())


@router.callback_query(F.data.startswith('category_'))
async def category(callback: CallbackQuery):
    await callback.answer('Вы выбрали категорию')
    await callback.message.answer(
        'Выберите категорию',
        reply_markup=await kb.personals(callback.data.split('_')[1]))


@router.callback_query(F.data.startswith('personal_'))
async def personal(callback: CallbackQuery):
    personal_data = await rq.get_personal(callback.data.split('_')[1])
    await callback.answer('Вы выбрали персону')
    await callback.message.answer(f'Фамилия: {personal_data.surname}\nИмя: {personal_data.name}\nОтчество: {personal_data.name_2})',
                                  reply_markup=await kb.personals(callback.data.split('_')[1]))
