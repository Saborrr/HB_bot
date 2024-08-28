from sqlalchemy import Column, Integer, Date, String
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
        query = select(Employee).where(text(f"SUBSTR(birth_date, 4, 2) = '{month_str}'"))
        result = await session.execute(query)
        employees = result.scalars().all()
        # Преобразуем строки дат в объекты datetime.date
        # с учетом правильного формата
        for employee in employees:
            try:
                employee.birth_date = datetime.strptime(employee.birth_date, "%d.%m.%Y").date()
            except ValueError as e:
                # Обработка ошибки, если дата имеет неправильный формат
                print(f"Ошибка преобразования даты для {employee.full_name}: {e}")
                raise
        return employees

    @staticmethod
    async def get_by_today(session: AsyncSession):
        today = date.today()
        query = select(Employee).where(
            Employee.birth_date.month == today.month,
            Employee.birth_date.day == today.day)
        result = await session.execute(query)
        return result.scalars().all()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
