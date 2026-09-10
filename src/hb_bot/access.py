from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


def is_private_allowed(
    user_id: int | None,
    chat_type: str | None,
    allowed_users: frozenset[int],
) -> bool:
    return user_id is not None and chat_type == "private" and user_id in allowed_users


class AccessMiddleware(BaseMiddleware):
    """Deny every message and callback outside the private allowlist."""

    def __init__(self, allowed_users: frozenset[int]) -> None:
        self.allowed_users = allowed_users

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        chat = data.get("event_chat")
        if is_private_allowed(
            getattr(user, "id", None),
            getattr(chat, "type", None),
            self.allowed_users,
        ):
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            await event.answer("Доступ запрещён", show_alert=True)
        elif isinstance(event, Message):
            await event.answer("Бот доступен только разрешённым пользователям в личном чате.")
        return None
