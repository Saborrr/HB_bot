from datetime import date, timedelta

import pytest

from hb_bot.birthdays import (
    Birthday,
    age_on,
    birthday_occurrence,
    days_until,
    parse_birth_date,
    years_word,
)


def test_parse_birth_date_with_optional_year():
    assert parse_birth_date("03.12") == Birthday(day=3, month=12, year=None)
    assert parse_birth_date("29.02.2000") == Birthday(day=29, month=2, year=2000)


@pytest.mark.parametrize("value", ["", "31.02", "00.10.1990", "1.2", "01.01.99", "01.01.0000"])
def test_parse_birth_date_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        parse_birth_date(value)


@pytest.mark.parametrize("year", [1899, date.today().year + 1])
def test_parse_birth_date_rejects_implausible_or_future_year(year):
    with pytest.raises(ValueError):
        parse_birth_date(f"01.01.{year:04d}")


def test_parse_birth_date_rejects_future_day_in_current_year():
    future = date.today() + timedelta(days=1)
    if future.year != date.today().year:
        pytest.skip("No later date exists in the current calendar year")

    with pytest.raises(ValueError):
        parse_birth_date(future.strftime("%d.%m.%Y"))


def test_february_29_uses_february_28_in_non_leap_year():
    birthday = Birthday(day=29, month=2, year=2000)
    assert birthday_occurrence(birthday, 2025) == date(2025, 2, 28)


def test_days_until_wraps_to_next_year():
    assert days_until(Birthday(2, 1), date(2026, 12, 31)) == 2


def test_age_is_calculated_for_occurrence_date():
    assert age_on(Birthday(10, 9, 2000), date(2026, 9, 9)) == 25
    assert age_on(Birthday(10, 9, 2000), date(2026, 9, 10)) == 26
    assert age_on(Birthday(10, 9), date(2026, 9, 10)) is None


@pytest.mark.parametrize(
    ("age", "word"), [(1, "год"), (2, "года"), (5, "лет"), (11, "лет"), (21, "год")]
)
def test_years_word_uses_russian_plural_rules(age, word):
    assert years_word(age) == word
