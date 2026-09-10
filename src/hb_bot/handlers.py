from __future__ import annotations

from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from hb_bot.config import Settings
from hb_bot.db.repository import EmployeeRepository
from hb_bot.keyboards import MONTHS, months_keyboard
from hb_bot.messages import chunk_message
from hb_bot.presentation import format_employee, format_upcoming_employee

router = Router(name="birthdays")

WELCOME = (
    "🎂 Бот напоминает о днях рождения коллег.\n\n"
    "/today — дни рождения сегодня\n"
    "/upcoming — ближайшие дни рождения\n"
    "/months — календарь по месяцам\n"
    "/find Иванов — поиск по имени или фамилии\n"
    "/help — справка"
)

HELP = (
    "Команды:\n"
    "/today — кто празднует сегодня\n"
    "/upcoming — события на ближайшие дни\n"
    "/months — выбрать месяц\n"
    "/find <имя или фамилия> — найти сотрудника\n\n"
    "Бот работает только в личном чате и только для пользователей из allowlist. "
    "По умолчанию год рождения и возраст не показываются."
)


async def _send_chunks(message: Message, header: str, lines: list[str]) -> None:
    for chunk in chunk_message(header, lines):
        await message.answer(chunk)


@router.message(CommandStart())
async def start_command(message: Message) -> None:
    await message.answer(WELCOME, reply_markup=months_keyboard())


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(HELP)


@router.message(Command("months"))
async def months_command(message: Message) -> None:
    await message.answer("Выберите месяц:", reply_markup=months_keyboard())


@router.callback_query(F.data.startswith("month:"))
async def month_callback(
    callback: CallbackQuery,
    session_factory: async_sessionmaker,
) -> None:
    await callback.answer()
    if not isinstance(callback.message, Message) or callback.data is None:
        return
    try:
        month = int(callback.data.removeprefix("month:"))
        if month not in range(1, 13):
            raise ValueError
    except ValueError:
        await callback.message.answer("Некорректный номер месяца.")
        return

    async with session_factory() as session:
        employees = await EmployeeRepository(session).for_month(month)
    if not employees:
        await callback.message.edit_text(f"В месяце «{MONTHS[month - 1]}» дней рождения нет.")
        return
    chunks = chunk_message(
        f"🎂 {MONTHS[month - 1]}",
        [format_employee(employee) for employee in employees],
    )
    await callback.message.edit_text(chunks[0])
    for chunk in chunks[1:]:
        await callback.message.answer(chunk)


@router.message(Command("today"))
async def today_command(
    message: Message,
    session_factory: async_sessionmaker,
    settings: Settings,
) -> None:
    today = datetime.now(settings.timezone).date()
    async with session_factory() as session:
        employees = await EmployeeRepository(session).today(today)
    if not employees:
        await message.answer("Сегодня дней рождения нет.")
        return
    await _send_chunks(message, "🎉 Сегодня", [format_employee(item) for item in employees])


@router.message(Command("upcoming"))
async def upcoming_command(
    message: Message,
    session_factory: async_sessionmaker,
    settings: Settings,
) -> None:
    today = datetime.now(settings.timezone).date()
    async with session_factory() as session:
        employees = await EmployeeRepository(session).upcoming(today, days=settings.upcoming_days)
    if not employees:
        await message.answer(f"В ближайшие {settings.upcoming_days} дней событий нет.")
        return
    await _send_chunks(
        message,
        f"🗓 Ближайшие {settings.upcoming_days} дней",
        [format_upcoming_employee(item, today) for item in employees],
    )


@router.message(Command("find"))
async def find_command(
    message: Message,
    command: CommandObject,
    session_factory: async_sessionmaker,
) -> None:
    query = " ".join((command.args or "").split())
    if len(query) < 2:
        await message.answer("Укажите минимум 2 символа, например: /find Иванов")
        return
    async with session_factory() as session:
        employees = await EmployeeRepository(session).search(query)
    if not employees:
        await message.answer("Ничего не найдено.")
        return
    await _send_chunks(
        message,
        "🔎 Результаты поиска",
        [format_employee(item) for item in employees],
    )
