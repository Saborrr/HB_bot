from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)

from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Главное меню')],
    [KeyboardButton(text='Настройки'), KeyboardButton(text='Контакты')]
], resize_keyboard=True, input_field_placeholder='Выберите пункт меню.')

months = ['Январь', 'Февраль', 'Март',
          'Апрель', 'Май', 'Июнь',
          'Июль', 'Август', 'Сентябрь',
          'Октябрь', 'Ноябрь', 'Декарбь']


async def inline_months():
    keyboard = InlineKeyboardBuilder()
    for month in months:
        keyboard.add(InlineKeyboardButton(text=month,
                                          url='http://www.dj-soft.narod.ru'))
    return keyboard.adjust(3).as_markup()
