from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date

_DATE_PATTERN = re.compile(r"^(\d{2})\.(\d{2})(?:\.(\d{4}))?$")


@dataclass(frozen=True, slots=True)
class Birthday:
    day: int
    month: int
    year: int | None = None

    def __post_init__(self) -> None:
        if self.year is not None and not 1900 <= self.year <= date.today().year:
            raise ValueError("Invalid birthday year")
        validation_year = self.year if self.year is not None else 2000
        try:
            validated_date = date(validation_year, self.month, self.day)
        except ValueError as error:
            raise ValueError("Invalid birthday") from error
        if self.year is not None and validated_date > date.today():
            raise ValueError("Birthday cannot be in the future")


def parse_birth_date(value: str) -> Birthday:
    match = _DATE_PATTERN.fullmatch(value.strip())
    if not match:
        raise ValueError("Use DD.MM or DD.MM.YYYY")
    day, month, year = match.groups()
    return Birthday(day=int(day), month=int(month), year=int(year) if year else None)


def birthday_occurrence(birthday: Birthday, year: int) -> date:
    if birthday.month == 2 and birthday.day == 29 and not calendar.isleap(year):
        return date(year, 2, 28)
    return date(year, birthday.month, birthday.day)


def next_occurrence(birthday: Birthday, today: date) -> date:
    occurrence = birthday_occurrence(birthday, today.year)
    if occurrence < today:
        occurrence = birthday_occurrence(birthday, today.year + 1)
    return occurrence


def days_until(birthday: Birthday, today: date) -> int:
    return (next_occurrence(birthday, today) - today).days


def age_on(birthday: Birthday, on_date: date) -> int | None:
    if birthday.year is None:
        return None
    years = on_date.year - birthday.year
    before_birthday = (on_date.month, on_date.day) < (birthday.month, birthday.day)
    return years - int(before_birthday)


def years_word(age: int) -> str:
    if age % 100 in range(11, 15):
        return "лет"
    if age % 10 == 1:
        return "год"
    if age % 10 in range(2, 5):
        return "года"
    return "лет"
