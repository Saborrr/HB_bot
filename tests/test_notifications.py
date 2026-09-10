import asyncio
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import select

from hb_bot.db.models import Base, Employee, NotificationDelivery
from hb_bot.db.session import create_database
from hb_bot.notifications import (
    _claim_delivery,
    _complete_delivery,
    _release_delivery,
    run_notification_cycle_safely,
    send_due_notifications,
)


class FakeBot:
    def __init__(self):
        self.messages = []

    async def send_message(self, chat_id: int, text: str):
        self.messages.append((chat_id, text))


@pytest.fixture
async def notification_db(tmp_path):
    engine, factory = create_database(f"sqlite+aiosqlite:///{tmp_path / 'notifications.sqlite3'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with factory() as session:
        session.add(Employee(external_id="1", full_name="Иванов Иван", birth_day=10, birth_month=9))
        await session.commit()
    yield factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_notifications_are_sent_once_per_chat_event_and_offset(notification_db):
    bot = FakeBot()
    today = date(2026, 9, 9)

    first = await send_due_notifications(bot, notification_db, (100, 200), (7, 1, 0), today)
    second = await send_due_notifications(bot, notification_db, (100, 200), (7, 1, 0), today)

    assert first == 2
    assert second == 0
    assert len(bot.messages) == 2
    assert all("завтра" in text.lower() for _, text in bot.messages)
    async with notification_db() as session:
        deliveries = (await session.scalars(select(NotificationDelivery))).all()
    assert len(deliveries) == 2
    assert all(delivery.delivered_at is not None for delivery in deliveries)


@pytest.mark.asyncio
async def test_failed_send_is_not_marked_as_delivered(notification_db):
    class FailingBot:
        async def send_message(self, chat_id: int, text: str):
            raise RuntimeError("network")

    sent = await send_due_notifications(
        FailingBot(), notification_db, (100,), (1,), date(2026, 9, 9)
    )

    assert sent == 0
    async with notification_db() as session:
        deliveries = (await session.scalars(select(NotificationDelivery))).all()
    assert deliveries == []


@pytest.mark.asyncio
async def test_concurrent_notification_cycles_send_only_once(notification_db):
    bot = FakeBot()
    results = await asyncio.gather(
        send_due_notifications(bot, notification_db, (100,), (1,), date(2026, 9, 9)),
        send_due_notifications(bot, notification_db, (100,), (1,), date(2026, 9, 9)),
    )

    assert sum(results) == 1
    assert len(bot.messages) == 1


@pytest.mark.asyncio
async def test_safe_notification_cycle_contains_temporary_errors():
    calls = 0

    async def failing_sender(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise RuntimeError("temporary database failure")

    result = await run_notification_cycle_safely(
        failing_sender,
        object(),
        object(),
        (),
        (),
        date(2026, 9, 9),
    )

    assert result == 0
    assert calls == 1


@pytest.mark.asyncio
async def test_sqlite_foreign_keys_remove_delivery_with_employee(notification_db):
    await send_due_notifications(FakeBot(), notification_db, (100,), (1,), date(2026, 9, 9))
    async with notification_db() as session:
        employee = await session.scalar(select(Employee))
        await session.delete(employee)
        await session.commit()
    async with notification_db() as session:
        deliveries = (await session.scalars(select(NotificationDelivery))).all()

    assert deliveries == []


@pytest.mark.asyncio
async def test_stale_claim_owner_cannot_release_or_complete_reclaimed_delivery(notification_db):
    async with notification_db() as session:
        employee = await session.scalar(select(Employee))

    original = await _claim_delivery(
        notification_db,
        chat_id=100,
        employee_id=employee.id,
        occurrence_year=2026,
        reminder_offset=1,
    )
    assert original is not None

    async with notification_db() as session:
        delivery = await session.get(NotificationDelivery, original.delivery_id)
        delivery.claimed_at = datetime.now(UTC) - timedelta(hours=1)
        await session.commit()

    replacement = await _claim_delivery(
        notification_db,
        chat_id=100,
        employee_id=employee.id,
        occurrence_year=2026,
        reminder_offset=1,
    )
    assert replacement is not None
    assert replacement.delivery_id == original.delivery_id
    assert replacement.owner_token != original.owner_token

    await _release_delivery(notification_db, original)
    await _complete_delivery(notification_db, original)

    async with notification_db() as session:
        delivery = await session.get(NotificationDelivery, replacement.delivery_id)
        assert delivery is not None
        assert delivery.owner_token == replacement.owner_token
        assert delivery.delivered_at is None

    await _complete_delivery(notification_db, replacement)
    async with notification_db() as session:
        delivery = await session.get(NotificationDelivery, replacement.delivery_id)
        assert delivery.delivered_at is not None
