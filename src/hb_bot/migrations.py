from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from hb_bot.config import DatabaseSettings


def run_migrations(database_url: str) -> None:
    migration_root = Path(__file__).with_name("alembic")
    config = Config()
    config.set_main_option("script_location", str(migration_root))
    config.attributes["database_url"] = database_url
    command.upgrade(config, "head")


def run_cli() -> None:
    run_migrations(DatabaseSettings().database_url)
