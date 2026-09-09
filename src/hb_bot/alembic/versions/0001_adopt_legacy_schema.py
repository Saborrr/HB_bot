"""Adopt or create the legacy employees table.

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

LEGACY_COLUMNS = {"id", "full_name", "birth_date", "age"}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("employees"):
        op.create_table(
            "employees",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("full_name", sa.String(), nullable=True),
            sa.Column("birth_date", sa.String(), nullable=True),
            sa.Column("age", sa.Integer(), nullable=True),
        )
        return

    columns = {column["name"] for column in inspector.get_columns("employees")}
    primary_key = set(inspector.get_pk_constraint("employees").get("constrained_columns") or [])
    if columns != LEGACY_COLUMNS or primary_key != {"id"}:
        raise RuntimeError(
            "Existing employees table is not the supported legacy schema; migration aborted"
        )


def downgrade() -> None:
    raise RuntimeError(
        "Revision 0001 may adopt an existing table and is intentionally irreversible"
    )
