from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import app.keyboards as kb
from app.database.models import Employee, SessionLocal, is_allowed
from datetime import datetime as dt


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Проверяем, есть ли доступ у пользователя"""
    user_id = message.from_user.id
    if not is_allowed(user_id):
        await message.reply("У вас нет доступа к этому боту ⛔️.")
    else:
        """Функция приветствия."""
        text = (f"{message.from_user.full_name}, приветствуем Вас 😊\n"
                "/today - показать у кого сегодня ДР\n"
                "/months - список ДР по месяцам"
                )
        await message.answer(text=text, reply_markup=await kb.inline_months())


@router.message(Command("months"))
async def birthdays_command(message: types.Message):
    keyboard = await kb.inline_months()
    await message.answer("Выберите месяц:", reply_markup=keyboard)


@router.callback_query(lambda c: c.data.isdigit())
async def birthdays_by_month(callback_query: CallbackQuery, state: FSMContext):
    """
    Преобразование данных callback запроса в целое число,
    представляющее номер месяца.
    """
    month = int(callback_query.data)
    """
    Открытие сессии базы данных с использованием контекстного менеджера.
    """
    async with SessionLocal() as session:
        """
        Получение списка сотрудников с днями рождения в указанном месяце.
        """
        employees = await Employee.get_by_month(session, month)
    """
    Формирование текста сообщения с информацией о днях рождения сотрудников.
    """
    if employees:
        employees.sort(key=lambda emp: emp.birth_date.day)
        text = "\n".join(
            [f"{emp.full_name} - {emp.birth_date.strftime('%d.%m.%Y')}"
             for emp in employees]
        )
    else:
        text = "В этом месяце нет дней рождения."
    await callback_query.message.edit_text(text)


@router.message(Command("today"))
async def birthdays_today_command(message: types.Message):
    """Функция вывода информации о дне рождения каждого сотрудника."""
    async with SessionLocal() as session:
        employees = await Employee.get_by_today(session)
    if employees:
        employees.sort(key=lambda emp: dt.strptime(
            emp.birth_date, '%d.%m.%Y').day)
        text = "\n".join([f"{emp.full_name} - {emp.age} лет"
                          for emp in employees])
    else:
        text = "Сегодня нет дней рождения."
    await message.answer(text)
