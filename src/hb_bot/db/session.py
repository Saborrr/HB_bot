from __future__ import annotations

from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine


def create_database(database_url: str) -> tuple[AsyncEngine, async_sessionmaker]:
    engine = create_async_engine(database_url, pool_pre_ping=True)
    if make_url(database_url).get_backend_name() == "sqlite":

        @event.listens_for(engine.sync_engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine, async_sessionmaker(engine, expire_on_commit=False)
