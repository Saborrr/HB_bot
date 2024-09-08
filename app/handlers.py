from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import app.keyboards as kb
from app.database.models import (Employee, calculate_age,
                                 find_employee_by_surname, SessionLocal,
                                 is_allowed)
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
                "/months - список ДР по месяцам\n"
                "/find Иванов - поиск сотрудника по фамилии\n"
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
    """Вывод информации о дне рождения каждого сотрудника."""
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


@router.message(Command("find"))
# Хендлер команды для поиска сотрудника
async def find_employee_command(message: types.Message):
    async with SessionLocal() as session:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await message.reply(
                "Пожалуйста, введите фамилию после команды, например:\n"
                "/find Иванов (фамилия обязательно с большой буквы)")
            return
        surname = parts[1].capitalize()
        # Поиск сотрудников с переданным аргументом `surname`
        employees = await find_employee_by_surname(session, surname)
        if employees:
            text = ""
            for emp in employees:
                birth_date = None
                try:
                    # Изменяем формат на '%d.%m.%Y', который соответствует БД
                    if isinstance(emp.birth_date, str):
                        birth_date = dt.strptime(emp.birth_date, "%d.%m.%Y")
                    elif isinstance(emp.birth_date, dt):
                        birth_date = emp.birth_date
                except ValueError as e:
                    print(f"Ошибка преобразования даты: {e}")

                age = calculate_age(birth_date) if birth_date else "неизвестен"
                calc_date = birth_date.strftime('%d.%m.%Y')
                calc_func = calc_date if birth_date else 'Неизвестно'
                text += (f"Сотрудник: {emp.full_name}\n"
                         f"Дата рождения: {calc_func}\n"
                         f"Возраст: {age} лет\n\n")
            await message.reply(text)
        else:
            await message.reply(f"Сотрудник с фамилией {surname} не найден.\n")
