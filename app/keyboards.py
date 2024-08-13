from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)

from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from app.database.requests import get_categories, get_category_personal

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Главное меню')],
    [KeyboardButton(text='Месяц'), KeyboardButton(text='Сегодня')]
], resize_keyboard=True, input_field_placeholder='Выберите пункт меню.')

months = ['Январь', 'Февраль', 'Март',
          'Апрель', 'Май', 'Июнь',
          'Июль', 'Август', 'Сентябрь',
          'Октябрь', 'Ноябрь', 'Декарбь']


async def inline_months():
    keyboard = InlineKeyboardBuilder()
    for month in months:
        keyboard.add(InlineKeyboardButton(
            text=month,
            url='http://www.dj-soft.narod.ru'))
    return keyboard.adjust(3).as_markup()


async def categories():
    all_categories = await get_categories()
    keyboard = InlineKeyboardBuilder()
    for category in all_categories:
        keyboard.add(InlineKeyboardButton(
            text=category.name,
            callback_data=f"category_{category.id}"))
    keyboard.add(InlineKeyboardButton(text='На главную',
                                      callback_data='to_main'))
    return keyboard.adjust(3).as_markup()


async def personals(category_id):
    all_personals = await get_category_personal(category_id)
    keyboard = InlineKeyboardBuilder()
    for personal in all_personals:
        keyboard.add(InlineKeyboardButton(
            text=personal.name,
            callback_data=f"personal_{personal.id}"))
    keyboard.add(InlineKeyboardButton(
        text='На главную',
        callback_data='to_main'))
    return keyboard.adjust(3).as_markup()
