from app.database.models import async_session
from app.database.models import User, Category, Personal
from sqlalchemy import select


async def set_user(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()


async def get_categories():
    async with async_session() as session:
        return await session.scalars(select(Category))


async def get_category_personal(category_id):
    async with async_session() as session:
        return await session.scalars(select(Personal).where(
            Personal.category == category_id))
