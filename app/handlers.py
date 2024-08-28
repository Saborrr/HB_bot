from aiogram import Router, types

from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.keyboards import month_keyboard

from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app.database.models import Employee
from app.database.models import SessionLocal


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Функция приветствия."""
    text = (f'{message.from_user.full_name}, приветствуем Вас 😊\nИспользуй команду /birthdays для просмотра информации.')
    await message.answer(text=text)


@router.message(Command("birthdays"))
async def birthdays_command(message: types.Message):
    await message.answer("Выберите месяц:", reply_markup=month_keyboard())


@router.callback_query(lambda c: c.data.isdigit())
async def birthdays_by_month(callback_query: CallbackQuery, state: FSMContext):
    month = int(callback_query.data)
    async with SessionLocal() as session:
        employees = await Employee.get_by_month(session, month)
    if employees:
        text = "\n".join([f"{emp.full_name} - {emp.birth_date.strftime('%d.%m.%Y')} ({emp.age} лет)" for emp in employees])
    else:
        text = "В этом месяце нет дней рождения."
    await callback_query.message.edit_text(text)


@router.message(Command("today"))
async def birthdays_today_command(message: types.Message):
    today = datetime.today()
    async with SessionLocal() as session:
        employees = await Employee.get_by_today(session)
    if employees:
        text = "\n".join([f"{emp.full_name} - {emp.age} лет" for emp in employees])
    else:
        text = "Сегодня нет дней рождения."
    await message.answer(text)
