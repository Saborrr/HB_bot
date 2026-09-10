from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

MONTHS = (
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
)


def months_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for number, month in enumerate(MONTHS, start=1):
        builder.add(InlineKeyboardButton(text=month, callback_data=f"month:{number}"))
    return builder.adjust(3).as_markup()
