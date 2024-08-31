import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from app.handlers import router
from app.database.models import init_db
from dotenv import load_dotenv


bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher(storage=MemoryStorage())


async def main():
    # запускаем функцию init_db для создания базы данных
    await init_db()
    load_dotenv()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
