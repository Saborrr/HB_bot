import sqlite3
from datetime import date, timedelta

import pytest

from hb_bot.migrations import run_migrations


def test_migration_converts_legacy_employee_without_data_loss(tmp_path):
    database = tmp_path / "legacy.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE employees ("
        "id INTEGER PRIMARY KEY, full_name VARCHAR, birth_date VARCHAR, age INTEGER)"
    )
    connection.execute(
        "INSERT INTO employees (id, full_name, birth_date, age) VALUES (?, ?, ?, ?)",
        (7, "Иванов Иван", "15.09.1990", 35),
    )
    connection.commit()
    connection.close()

    run_migrations(f"sqlite+aiosqlite:///{database}")

    connection = sqlite3.connect(database)
    columns = {row[1] for row in connection.execute("PRAGMA table_info(employees)")}
    employee = connection.execute(
        "SELECT id, external_id, full_name, birth_day, birth_month, birth_year, legacy_age "
        "FROM employees"
    ).fetchone()
    notification_table = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='notification_deliveries'"
    ).fetchone()
    connection.close()

    assert columns == {
        "id",
        "external_id",
        "full_name",
        "birth_day",
        "birth_month",
        "birth_year",
        "legacy_age",
    }
    assert employee == (7, "legacy-7", "Иванов Иван", 15, 9, 1990, 35)
    assert notification_table == ("notification_deliveries",)


def test_invalid_legacy_data_leaves_original_schema_untouched_and_can_retry(tmp_path):
    database = tmp_path / "invalid.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE employees ("
        "id INTEGER PRIMARY KEY, full_name VARCHAR, birth_date VARCHAR, age INTEGER)"
    )
    connection.execute(
        "INSERT INTO employees (id, full_name, birth_date, age) VALUES (1, 'Test', '31.02.2020', 6)"
    )
    connection.commit()
    connection.close()

    with pytest.raises(RuntimeError, match="employee IDs: \\[1\\]"):
        run_migrations(f"sqlite+aiosqlite:///{database}")

    connection = sqlite3.connect(database)
    columns = {row[1] for row in connection.execute("PRAGMA table_info(employees)")}
    version = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    connection.execute("UPDATE employees SET birth_date='28.02.2020' WHERE id=1")
    connection.commit()
    connection.close()
    assert columns == {"id", "full_name", "birth_date", "age"}
    assert version == "0001"

    run_migrations(f"sqlite+aiosqlite:///{database}")


def test_migration_accepts_yearless_leap_day(tmp_path):
    database = tmp_path / "leap-day.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE employees ("
        "id INTEGER PRIMARY KEY, full_name VARCHAR, birth_date VARCHAR, age INTEGER)"
    )
    connection.execute(
        "INSERT INTO employees (id, full_name, birth_date, age) VALUES (1, 'Test', '29.02', NULL)"
    )
    connection.commit()
    connection.close()

    run_migrations(f"sqlite+aiosqlite:///{database}")

    connection = sqlite3.connect(database)
    birthday = connection.execute(
        "SELECT birth_day, birth_month, birth_year FROM employees"
    ).fetchone()
    connection.close()
    assert birthday == (29, 2, None)


def test_migration_rejects_future_day_in_current_year_before_schema_changes(tmp_path):
    future = date.today() + timedelta(days=1)
    if future.year != date.today().year:
        pytest.skip("No later date exists in the current calendar year")
    database = tmp_path / "future-date.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE employees ("
        "id INTEGER PRIMARY KEY, full_name VARCHAR, birth_date VARCHAR, age INTEGER)"
    )
    connection.execute(
        "INSERT INTO employees (id, full_name, birth_date, age) VALUES (1, 'Test', ?, NULL)",
        (future.strftime("%d.%m.%Y"),),
    )
    connection.commit()
    connection.close()

    with pytest.raises(RuntimeError, match="employee IDs: \\[1\\]"):
        run_migrations(f"sqlite+aiosqlite:///{database}")

    connection = sqlite3.connect(database)
    columns = {row[1] for row in connection.execute("PRAGMA table_info(employees)")}
    version = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    connection.close()
    assert columns == {"id", "full_name", "birth_date", "age"}
    assert version == "0001"
