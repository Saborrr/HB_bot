from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import uuid4

from aiogram import Bot
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker

from hb_bot.birthdays import days_until, next_occurrence
from hb_bot.db.models import NotificationDelivery
from hb_bot.db.repository import EmployeeRepository

logger = logging.getLogger(__name__)
CLAIM_TIMEOUT = timedelta(minutes=15)


@dataclass(frozen=True, slots=True)
class DeliveryClaim:
    delivery_id: int
    owner_token: str


def reminder_text(full_name: str, offset: int) -> str:
    if offset == 0:
        return f"🎉 Сегодня день рождения у {full_name}!"
    if offset == 1:
        return f"🎁 Завтра день рождения у {full_name}."
    return f"🎁 Через {offset} дн. день рождения у {full_name}."


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


async def _claim_delivery(
    session_factory: async_sessionmaker,
    *,
    chat_id: int,
    employee_id: int,
    occurrence_year: int,
    reminder_offset: int,
) -> DeliveryClaim | None:
    now = datetime.now(UTC)
    owner_token = str(uuid4())
    async with session_factory() as session:
        delivery = NotificationDelivery(
            chat_id=chat_id,
            employee_id=employee_id,
            occurrence_year=occurrence_year,
            reminder_offset=reminder_offset,
            claimed_at=now,
            owner_token=owner_token,
        )
        session.add(delivery)
        try:
            await session.commit()
            return DeliveryClaim(delivery.id, owner_token)
        except IntegrityError:
            await session.rollback()

        existing = await session.scalar(
            select(NotificationDelivery).where(
                NotificationDelivery.chat_id == chat_id,
                NotificationDelivery.employee_id == employee_id,
                NotificationDelivery.occurrence_year == occurrence_year,
                NotificationDelivery.reminder_offset == reminder_offset,
            )
        )
        if existing is None or existing.delivered_at is not None:
            return None
        if _as_utc(existing.claimed_at) > now - CLAIM_TIMEOUT:
            return None

        result = await session.execute(
            update(NotificationDelivery)
            .where(
                NotificationDelivery.id == existing.id,
                NotificationDelivery.claimed_at == existing.claimed_at,
                NotificationDelivery.delivered_at.is_(None),
            )
            .values(claimed_at=now, owner_token=owner_token)
        )
        await session.commit()
        return DeliveryClaim(existing.id, owner_token) if result.rowcount == 1 else None


async def _release_delivery(session_factory: async_sessionmaker, claim: DeliveryClaim) -> None:
    async with session_factory() as session:
        await session.execute(
            delete(NotificationDelivery).where(
                NotificationDelivery.id == claim.delivery_id,
                NotificationDelivery.owner_token == claim.owner_token,
                NotificationDelivery.delivered_at.is_(None),
            )
        )
        await session.commit()


async def _complete_delivery(session_factory: async_sessionmaker, claim: DeliveryClaim) -> None:
    async with session_factory() as session:
        await session.execute(
            update(NotificationDelivery)
            .where(
                NotificationDelivery.id == claim.delivery_id,
                NotificationDelivery.owner_token == claim.owner_token,
                NotificationDelivery.delivered_at.is_(None),
            )
            .values(delivered_at=datetime.now(UTC))
        )
        await session.commit()


async def send_due_notifications(
    bot: Bot,
    session_factory: async_sessionmaker,
    chat_ids: Sequence[int],
    reminder_days: Sequence[int],
    today: date,
) -> int:
    """Reserve, send and journal reminders without concurrent duplicates."""

    sent = 0
    async with session_factory() as session:
        employees = await EmployeeRepository(session).all()

    for employee in employees:
        offset = days_until(employee.birthday, today)
        if offset not in reminder_days:
            continue
        occurrence_year = next_occurrence(employee.birthday, today).year
        for chat_id in chat_ids:
            claim = await _claim_delivery(
                session_factory,
                chat_id=chat_id,
                employee_id=employee.id,
                occurrence_year=occurrence_year,
                reminder_offset=offset,
            )
            if claim is None:
                continue
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=reminder_text(employee.full_name, offset),
                )
            except Exception:
                logger.exception("Birthday reminder delivery failed")
                await _release_delivery(session_factory, claim)
                continue
            await _complete_delivery(session_factory, claim)
            sent += 1
    return sent


async def run_notification_cycle_safely(
    sender: Callable[..., Awaitable[int]],
    bot: Any,
    session_factory: Any,
    chat_ids: Sequence[int],
    reminder_days: Sequence[int],
    today: date,
) -> int:
    try:
        return await sender(bot, session_factory, chat_ids, reminder_days, today)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("Birthday notification cycle failed; scheduler will continue")
        return 0


def seconds_until_next_run(now: datetime, notify_hour: int, notify_minute: int) -> float:
    target = now.replace(hour=notify_hour, minute=notify_minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


async def notification_loop(
    bot: Bot,
    session_factory: async_sessionmaker,
    chat_ids: Sequence[int],
    reminder_days: Sequence[int],
    notify_hour: int,
    notify_minute: int,
    timezone,
) -> None:
    while True:
        now = datetime.now(timezone)
        await asyncio.sleep(seconds_until_next_run(now, notify_hour, notify_minute))
        local_today = datetime.now(timezone).date()
        await run_notification_cycle_safely(
            send_due_notifications,
            bot,
            session_factory,
            chat_ids,
            reminder_days,
            local_today,
        )
