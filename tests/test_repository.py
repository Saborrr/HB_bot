from datetime import date

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from hb_bot.birthdays import Birthday
from hb_bot.db.models import Base, Employee
from hb_bot.db.repository import EmployeeRepository
from hb_bot.importer import ImportRecord, apply_import


@pytest.fixture
async def session_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


@pytest.mark.asyncio
async def test_repository_search_treats_sql_wildcards_as_text(session_factory):
    async with session_factory() as session:
        session.add_all(
            [
                Employee(external_id="1", full_name="Иванов Иван", birth_day=1, birth_month=1),
                Employee(external_id="2", full_name="Петрова Анна", birth_day=2, birth_month=2),
            ]
        )
        await session.commit()
        repository = EmployeeRepository(session)

        assert await repository.search("%") == []
        assert [item.full_name for item in await repository.search("иванов")] == ["Иванов Иван"]


@pytest.mark.asyncio
async def test_repository_rejects_invalid_month(session_factory):
    async with session_factory() as session:
        with pytest.raises(ValueError):
            await EmployeeRepository(session).for_month(13)


@pytest.mark.asyncio
async def test_csv_import_is_idempotent_upsert(session_factory):
    first = [ImportRecord("e-1", "Иванов Иван", Birthday(15, 9, 1990))]
    updated = [ImportRecord("e-1", "Иванов Иван Петрович", Birthday(16, 9, 1990))]

    async with session_factory() as session:
        assert await apply_import(session, first) == (1, 0)
        assert await apply_import(session, updated) == (0, 1)
        rows = await EmployeeRepository(session).all()

    assert len(rows) == 1
    assert rows[0].full_name == "Иванов Иван Петрович"
    assert rows[0].birthday == Birthday(16, 9, 1990)


@pytest.mark.asyncio
async def test_repository_finds_upcoming_across_year_boundary(session_factory):
    async with session_factory() as session:
        session.add_all(
            [
                Employee(external_id="1", full_name="Первый", birth_day=31, birth_month=12),
                Employee(external_id="2", full_name="Второй", birth_day=2, birth_month=1),
                Employee(external_id="3", full_name="Дальний", birth_day=20, birth_month=1),
            ]
        )
        await session.commit()
        rows = await EmployeeRepository(session).upcoming(date(2026, 12, 30), days=5)

    assert [row.full_name for row in rows] == ["Первый", "Второй"]
