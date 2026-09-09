from __future__ import annotations

import asyncio
import contextlib
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from hb_bot.access import AccessMiddleware
from hb_bot.config import Settings
from hb_bot.db.session import create_database
from hb_bot.handlers import router
from hb_bot.notifications import (
    notification_loop,
    run_notification_cycle_safely,
    send_due_notifications,
)

logger = logging.getLogger(__name__)

COMMANDS = [
    BotCommand(command="today", description="Дни рождения сегодня"),
    BotCommand(command="upcoming", description="Ближайшие дни рождения"),
    BotCommand(command="months", description="Календарь по месяцам"),
    BotCommand(command="find", description="Поиск сотрудника"),
    BotCommand(command="help", description="Справка"),
]


def build_dispatcher(settings: Settings) -> Dispatcher:
    dispatcher = Dispatcher()
    access = AccessMiddleware(settings.allowed_users)
    dispatcher.message.outer_middleware(access)
    dispatcher.callback_query.outer_middleware(access)
    dispatcher.include_router(router)
    return dispatcher


async def main() -> None:
    settings = Settings()
    settings.validate_runtime_values()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    engine, session_factory = create_database(settings.database_url)
    bot = Bot(token=settings.bot_token.get_secret_value())
    dispatcher = build_dispatcher(settings)
    scheduler_task: asyncio.Task | None = None

    try:
        await bot.set_my_commands(COMMANDS)
        if settings.notify_chat_ids:
            await run_notification_cycle_safely(
                send_due_notifications,
                bot,
                session_factory,
                settings.notify_chat_ids,
                settings.reminder_days,
                datetime.now(settings.timezone).date(),
            )
            scheduler_task = asyncio.create_task(
                notification_loop(
                    bot,
                    session_factory,
                    settings.notify_chat_ids,
                    settings.reminder_days,
                    settings.notify_time.hour,
                    settings.notify_time.minute,
                    settings.timezone,
                ),
                name="birthday-notifications",
            )
        await dispatcher.start_polling(
            bot,
            settings=settings,
            session_factory=session_factory,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
    finally:
        if scheduler_task is not None:
            scheduler_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await scheduler_task
        await bot.session.close()
        await engine.dispose()


def run() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
