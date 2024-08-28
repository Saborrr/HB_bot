import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import TOKEN
from app.handlers import router
from app.database.models import init_db


bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


async def main():
    # запускаем функцию async_main для создания базы данных
    await init_db()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
