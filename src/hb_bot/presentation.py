from __future__ import annotations

from datetime import date

from hb_bot.birthdays import age_on, days_until, years_word
from hb_bot.db.models import Employee

_MONTHS = (
    "",
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)


def format_employee(
    employee: Employee,
    *,
    show_birth_year: bool = False,
    on_date: date | None = None,
) -> str:
    birthday = employee.birthday
    result = f"{employee.full_name} — {birthday.day} {_MONTHS[birthday.month]}"
    if show_birth_year and birthday.year is not None:
        result += f" {birthday.year}"
        if on_date is not None:
            age = age_on(birthday, on_date)
            if age is not None:
                result += f" · {age} {years_word(age)}"
    return result


def format_upcoming_employee(employee: Employee, today: date) -> str:
    offset = days_until(employee.birthday, today)
    if offset == 0:
        prefix = "Сегодня"
    elif offset == 1:
        prefix = "Завтра"
    else:
        prefix = f"Через {offset} дн."
    return f"{prefix} · {format_employee(employee)}"
