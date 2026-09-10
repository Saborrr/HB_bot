from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from hb_bot.birthdays import Birthday


class Base(DeclarativeBase):
    pass


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("external_id", name="uq_employees_external_id"),
        CheckConstraint(
            "((birth_month IN (1, 3, 5, 7, 8, 10, 12) AND birth_day BETWEEN 1 AND 31) "
            "OR (birth_month IN (4, 6, 9, 11) AND birth_day BETWEEN 1 AND 30) "
            "OR (birth_month = 2 AND birth_day BETWEEN 1 AND 29))",
            name="ck_employees_valid_month_day",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    birth_day: Mapped[int] = mapped_column(Integer, nullable=False)
    birth_month: Mapped[int] = mapped_column(Integer, nullable=False)
    birth_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    legacy_age: Mapped[int | None] = mapped_column(Integer, nullable=True)

    @property
    def birthday(self) -> Birthday:
        return Birthday(self.birth_day, self.birth_month, self.birth_year)


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"
    __table_args__ = (
        UniqueConstraint(
            "chat_id",
            "employee_id",
            "occurrence_year",
            "reminder_offset",
            name="uq_notification_delivery_event",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    occurrence_year: Mapped[int] = mapped_column(nullable=False)
    reminder_offset: Mapped[int] = mapped_column(nullable=False)
    claimed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    owner_token: Mapped[str] = mapped_column(String(36), nullable=False)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
