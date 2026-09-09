"""Normalize birthdays and add notification delivery journal.

Revision ID: 0002
Revises: 0001
"""

from datetime import date

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


LEGACY_COLUMNS = {"id", "full_name", "birth_date", "age"}
VALID_MONTH_DAY = """(
    (birth_month IN (1, 3, 5, 7, 8, 10, 12) AND birth_day BETWEEN 1 AND 31)
 OR (birth_month IN (4, 6, 9, 11) AND birth_day BETWEEN 1 AND 30)
 OR (birth_month = 2 AND birth_day BETWEEN 1 AND 29)
)"""


def _parse_legacy_date(value: str | None) -> tuple[int, int, int | None]:
    if not value:
        raise ValueError("empty date")
    parts = value.split(".")
    if len(parts) not in {2, 3} or any(not part.isdigit() for part in parts):
        raise ValueError("unsupported date format")
    if len(parts[0]) != 2 or len(parts[1]) != 2 or (len(parts) == 3 and len(parts[2]) != 4):
        raise ValueError("unsupported date format")
    day, month = int(parts[0]), int(parts[1])
    year = int(parts[2]) if len(parts) == 3 else None
    if year is not None and not 1900 <= year <= date.today().year:
        raise ValueError("invalid year")
    validated_date = date(year if year is not None else 2000, month, day)
    if year is not None and validated_date > date.today():
        raise ValueError("future date")
    return day, month, year


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("employees")}
    if columns != LEGACY_COLUMNS:
        raise RuntimeError(
            "Unsupported employees schema at revision 0001; restore the expected legacy backup"
        )
    if inspector.has_table("notification_deliveries"):
        raise RuntimeError(
            "notification_deliveries already exists before revision 0002; refusing to overwrite it"
        )

    # Validate every row before the first DDL statement. This is essential on
    # SQLite, whose ALTER TABLE operations cannot be rolled back reliably.
    invalid_ids: list[int] = []
    prepared: list[dict[str, object]] = []
    rows = bind.execute(
        sa.text("SELECT id, full_name, birth_date, age FROM employees ORDER BY id")
    ).fetchall()
    for employee_id, full_name, legacy_date, legacy_age in rows:
        try:
            day, month, year = _parse_legacy_date(legacy_date)
            if not full_name or len(full_name) > 255:
                raise ValueError("invalid full name")
        except (TypeError, ValueError):
            invalid_ids.append(employee_id)
            continue
        prepared.append(
            {
                "employee_id": employee_id,
                "external_id": f"legacy-{employee_id}",
                "day": day,
                "month": month,
                "year": year,
                "legacy_age": legacy_age,
            }
        )
    if invalid_ids:
        raise RuntimeError(
            f"Cannot migrate invalid birth dates or names for employee IDs: {invalid_ids}"
        )

    with op.batch_alter_table("employees") as batch:
        batch.add_column(sa.Column("external_id", sa.String(length=128), nullable=True))
        batch.add_column(sa.Column("birth_day", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("birth_month", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("birth_year", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("legacy_age", sa.Integer(), nullable=True))

    for values in prepared:
        bind.execute(
            sa.text(
                "UPDATE employees SET external_id=:external_id, birth_day=:day, "
                "birth_month=:month, birth_year=:year, legacy_age=:legacy_age "
                "WHERE id=:employee_id"
            ),
            values,
        )

    with op.batch_alter_table("employees") as batch:
        batch.alter_column("external_id", existing_type=sa.String(length=128), nullable=False)
        batch.alter_column(
            "full_name", existing_type=sa.String(), type_=sa.String(length=255), nullable=False
        )
        batch.alter_column("birth_day", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("birth_month", existing_type=sa.Integer(), nullable=False)
        batch.create_unique_constraint("uq_employees_external_id", ["external_id"])
        batch.create_check_constraint("ck_employees_valid_month_day", VALID_MONTH_DAY)
        batch.drop_column("birth_date")
        batch.drop_column("age")

    op.create_index("ix_employees_full_name", "employees", ["full_name"])
    op.create_table(
        "notification_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("occurrence_year", sa.Integer(), nullable=False),
        sa.Column("reminder_offset", sa.Integer(), nullable=False),
        sa.Column(
            "claimed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("owner_token", sa.String(length=36), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "chat_id",
            "employee_id",
            "occurrence_year",
            "reminder_offset",
            name="uq_notification_delivery_event",
        ),
    )
    op.create_index(
        "ix_notification_deliveries_employee_id",
        "notification_deliveries",
        ["employee_id"],
    )


def downgrade() -> None:
    raise RuntimeError(
        "Revision 0002 is intentionally irreversible; restore the pre-migration backup instead"
    )
