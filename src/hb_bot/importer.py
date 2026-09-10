from __future__ import annotations

import argparse
import asyncio
import csv
import io
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hb_bot.birthdays import Birthday, parse_birth_date
from hb_bot.config import DatabaseSettings
from hb_bot.db.models import Employee
from hb_bot.db.session import create_database

_EXPECTED_HEADERS = ["external_id", "full_name", "birth_date"]


@dataclass(frozen=True, slots=True)
class ImportRecord:
    external_id: str
    full_name: str
    birthday: Birthday


@dataclass(frozen=True, slots=True)
class ImportPlan:
    records: list[ImportRecord]
    errors: list[str]


def parse_csv(content: str) -> ImportPlan:
    reader = csv.DictReader(io.StringIO(content.removeprefix("\ufeff")))
    if reader.fieldnames != _EXPECTED_HEADERS:
        return ImportPlan([], ["Ожидаются столбцы: external_id, full_name, birth_date"])

    records: list[ImportRecord] = []
    errors: list[str] = []
    seen: set[str] = set()
    row_count = 0
    for line_number, row in enumerate(reader, start=2):
        row_count += 1
        external_id = (row.get("external_id") or "").strip()
        full_name = " ".join((row.get("full_name") or "").split())
        birthday_text = (row.get("birth_date") or "").strip()
        row_errors: list[str] = []
        if None in row:
            row_errors.append("найдены лишние столбцы")
        if not external_id:
            row_errors.append("external_id обязателен")
        elif len(external_id) > 128:
            row_errors.append("external_id длиннее 128 символов")
        elif external_id in seen:
            row_errors.append("external_id повторяется")
        else:
            seen.add(external_id)
        if not full_name:
            row_errors.append("full_name обязателен")
        elif len(full_name) > 255:
            row_errors.append("full_name длиннее 255 символов")
        try:
            birthday = parse_birth_date(birthday_text)
        except ValueError:
            birthday = None
            row_errors.append("birth_date должна иметь формат ДД.ММ или ДД.ММ.ГГГГ")
        if row_errors:
            errors.append(f"строка {line_number}: " + "; ".join(row_errors))
        elif birthday is not None:
            records.append(ImportRecord(external_id, full_name, birthday))

    if row_count == 0:
        errors.append("CSV не содержит записей")
    return ImportPlan(records if not errors else [], errors)


async def apply_import(session: AsyncSession, records: list[ImportRecord]) -> tuple[int, int]:
    created = 0
    updated = 0
    try:
        for record in records:
            employee = await session.scalar(
                select(Employee).where(Employee.external_id == record.external_id)
            )
            if employee is None:
                employee = Employee(
                    external_id=record.external_id,
                    full_name=record.full_name,
                    birth_day=record.birthday.day,
                    birth_month=record.birthday.month,
                    birth_year=record.birthday.year,
                )
                session.add(employee)
                created += 1
            else:
                employee.full_name = record.full_name
                employee.birth_day = record.birthday.day
                employee.birth_month = record.birthday.month
                employee.birth_year = record.birthday.year
                updated += 1
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    return created, updated


async def import_file(path: Path) -> tuple[int, int]:
    settings = DatabaseSettings()
    content = await asyncio.to_thread(path.read_text, encoding="utf-8-sig")
    plan = parse_csv(content)
    if plan.errors:
        raise ValueError("\n".join(plan.errors))
    engine, session_factory = create_database(settings.database_url)
    try:
        async with session_factory() as session:
            return await apply_import(session, plan.records)
    finally:
        await engine.dispose()


def run() -> None:
    parser = argparse.ArgumentParser(description="Import employee birthdays from CSV")
    parser.add_argument("csv_file", type=Path)
    args = parser.parse_args()
    created, updated = asyncio.run(import_file(args.csv_file))
    print(f"Импорт завершён: добавлено {created}, обновлено {updated}")


if __name__ == "__main__":
    run()
