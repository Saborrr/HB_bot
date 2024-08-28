from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def month_keyboard():
    buttons = [
        [InlineKeyboardButton(text=str(month), callback_data=str(month))]
        for month in range(1, 13)
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard
