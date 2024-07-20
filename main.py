import asyncio
import logging

from aiogram import Bot, Dispatcher

from aiogram.filters import CommandStart
from aiogram.types import Message
from config import TOKEN


bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Функция приветствия."""
    text = (f'{message.from_user.full_name}, приветствуем Вас 😊\n')
    await message.answer(text=text)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
