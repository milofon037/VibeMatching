from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from bot.constants.menu_actions import MAIN_MENU_ACTIONS
from bot.utils.context import api_client, user_sessions


class UserActivityMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        from_user = getattr(event, "from_user", None)
        if from_user:
            try:
                await api_client.update_activity(telegram_id=from_user.id)
            except Exception:
                # Activity update should never block bot handlers.
                pass
        return await handler(event, data)


class ResetSessionOnMenuMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event.text, str) and event.text in MAIN_MENU_ACTIONS:
            user_sessions.pop(event.from_user.id, None)
        return await handler(event, data)
