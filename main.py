import asyncio

from aiogram import Bot, Dispatcher

from aiogram.filters import CommandStart
from aiogram.types import Message
from config import TOKEN


bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Hello, world!")


async def main():
    await dp.start_polling(bot)

    if __name__ == "__main__":
        asyncio.run(main())
        print("Bot started")
