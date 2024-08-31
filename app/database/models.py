from sqlalchemy import Column, Integer, String, func
from sqlalchemy.ext.asyncio import (AsyncSession, create_async_engine)
from sqlalchemy import select
from datetime import date, datetime
from sqlalchemy.orm import sessionmaker, declarative_base
from config import DATABASE_URL
from sqlalchemy.sql import text


engine = create_async_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine,
                            class_=AsyncSession)

Base = declarative_base()


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    birth_date = Column(String)
    age = Column(Integer)

    @staticmethod
    async def get_by_month(session: AsyncSession, month: int):
        month_str = f"{month:02d}"
        # SQL запрос для выбора строк по месяцу
        query = select(Employee).where(
            text(f"SUBSTR(birth_date, 4, 2) = '{month_str}'"))
        result = await session.execute(query)
        employees = result.scalars().all()
        # Преобразуем строки дат в объекты datetime.date
        # с учетом правильного формата
        for employee in employees:
            try:
                employee.birth_date = datetime.strptime(
                    employee.birth_date, "%d.%m.%Y").date()
            except ValueError as e:
                # Обработка ошибки, если дата имеет неправильный формат
                print(f"Ошибка преобразования даты: {employee.full_name}: {e}")
                raise
        return employees

    @staticmethod
    async def get_by_today(session: AsyncSession):
        today = date.today()
        day_str = f"{today.day:02d}"
        month_str = f"{today.month:02d}"
        # Используем SQL функции для сравнения строк
        query = select(Employee).where(
            func.substr(Employee.birth_date, 1, 2) == day_str,
            func.substr(Employee.birth_date, 4, 2) == month_str
        )
        result = await session.execute(query)
        employees = result.scalars().all()
        # Рассчитываем возраст для каждого сотрудника
        for employee in employees:
            birth_date = datetime.strptime(
                employee.birth_date, "%d.%m.%Y").date()
            calclc_age_year = today.year - birth_date.year
            calclc_age_month_and_day = (
                today.month, today.day) < (birth_date.month, birth_date.day)
            employee.age = calclc_age_year - calclc_age_month_and_day
        return employees


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
