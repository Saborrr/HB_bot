from datetime import date

from hb_bot.db.models import Employee
from hb_bot.presentation import format_employee, format_upcoming_employee


def employee() -> Employee:
    return Employee(
        external_id="e-1",
        full_name="Иванов <Иван>",
        birth_day=15,
        birth_month=9,
        birth_year=1990,
    )


def test_employee_format_hides_birth_year_by_default():
    text = format_employee(employee())
    assert text == "Иванов <Иван> — 15 сентября"
    assert "1990" not in text


def test_employee_format_can_show_year_and_age_explicitly():
    text = format_employee(employee(), show_birth_year=True, on_date=date(2026, 9, 15))
    assert text == "Иванов <Иван> — 15 сентября 1990 · 36 лет"


def test_upcoming_format_uses_relative_label():
    text = format_upcoming_employee(employee(), date(2026, 9, 14))
    assert text == "Завтра · Иванов <Иван> — 15 сентября"
