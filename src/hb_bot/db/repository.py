from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hb_bot.birthdays import days_until
from hb_bot.db.models import Employee


class EmployeeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def all(self) -> list[Employee]:
        result = await self.session.scalars(select(Employee).order_by(Employee.full_name))
        return list(result)

    async def for_month(self, month: int) -> list[Employee]:
        if month not in range(1, 13):
            raise ValueError("month must be between 1 and 12")
        result = await self.session.scalars(
            select(Employee)
            .where(Employee.birth_month == month)
            .order_by(Employee.birth_day, Employee.full_name)
        )
        return list(result)

    async def today(self, today: date) -> list[Employee]:
        employees = await self.all()
        return [employee for employee in employees if days_until(employee.birthday, today) == 0]

    async def upcoming(self, today: date, *, days: int = 7) -> list[Employee]:
        if days < 0 or days > 366:
            raise ValueError("days must be between 0 and 366")
        employees = await self.all()
        due = [employee for employee in employees if days_until(employee.birthday, today) <= days]
        return sorted(
            due,
            key=lambda employee: (days_until(employee.birthday, today), employee.full_name),
        )

    async def search(self, term: str, *, limit: int = 20) -> list[Employee]:
        normalized = " ".join(term.split())
        if len(normalized) < 2 or len(normalized) > 100:
            return []
        # SQLite's built-in NOCASE collation only handles ASCII. Python casefold
        # keeps Cyrillic search consistent with PostgreSQL for this small directory.
        needle = normalized.casefold()
        employees = await self.all()
        return [employee for employee in employees if needle in employee.full_name.casefold()][
            :limit
        ]
