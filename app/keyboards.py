from aiogram.types import (InlineKeyboardButton, ReplyKeyboardMarkup,
                           KeyboardButton)
from aiogram.utils.keyboard import InlineKeyboardBuilder


main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Главное меню')],
    [KeyboardButton(text='Месяц'), KeyboardButton(text='Сегодня')]
], resize_keyboard=True, input_field_placeholder='Выберите пункт меню.')


months = {
      'Январь': 1,
      'Февраль': 2,
      'Март': 3,
      'Апрель': 4,
      'Май': 5,
      'Июнь': 6,
      'Июль': 7,
      'Август': 8,
      'Сентябрь': 9,
      'Октябрь': 10,
      'Ноябрь': 11,
      'Декарбь': 12
      }


async def inline_months():
    keyboard = InlineKeyboardBuilder()
    for month, month_num in months.items():
        keyboard.add(InlineKeyboardButton(
            text=month,
            callback_data=str(month_num)))  # Передаем номер месяца
    return keyboard.adjust(3).as_markup()
