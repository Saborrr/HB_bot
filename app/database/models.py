from sqlalchemy import BigInteger, Date, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import (AsyncAttrs, async_sessionmaker,
                                    create_async_engine)

engine = create_async_engine(url="sqlite+aiosqlite:///db.sqlite3")


# подключаем базу данных
async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(25))


class Personal(Base):
    __tablename__ = "personals"

    id: Mapped[int] = mapped_column(primary_key=True)
    surname: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(15))
    name_2: Mapped[str] = mapped_column(String(15))
    birthday: Mapped[Date] = mapped_column(Date)
    category: Mapped[int] = mapped_column(ForeignKey("categories.id"))


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
