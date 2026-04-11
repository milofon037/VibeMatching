"""Tests for bot middlewares."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import Message, User

from bot.middlewares.activity_and_session import (
    ResetSessionOnMenuMiddleware,
    UserActivityMiddleware,
)


@pytest.mark.asyncio
async def test_user_activity_middleware_updates_activity():
    """Test middleware updates user activity."""
    middleware = UserActivityMiddleware()

    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 123456789

    handler = AsyncMock()
    data = {}

    with patch("bot.middlewares.activity_and_session.api_client") as mock_api:
        mock_api.update_activity = AsyncMock(return_value=(200, {}))

        await middleware(handler, message, data)

        mock_api.update_activity.assert_called_once()
        handler.assert_called_once()


@pytest.mark.asyncio
async def test_user_activity_middleware_handles_callback():
    """Test middleware handles callback queries."""
    from aiogram.types import CallbackQuery

    middleware = UserActivityMiddleware()

    callback = MagicMock(spec=CallbackQuery)
    callback.from_user = MagicMock(spec=User)
    callback.from_user.id = 123456789

    handler = AsyncMock()
    data = {}

    with patch("bot.middlewares.activity_and_session.api_client") as mock_api:
        mock_api.update_activity = AsyncMock(return_value=(200, {}))

        await middleware(handler, callback, data)

        mock_api.update_activity.assert_called_once()
        handler.assert_called_once()


@pytest.mark.asyncio
async def test_user_activity_middleware_api_error():
    """Test middleware handles API errors gracefully."""
    middleware = UserActivityMiddleware()

    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 123456789

    handler = AsyncMock()
    data = {}

    with patch("bot.middlewares.activity_and_session.api_client") as mock_api:
        mock_api.update_activity = AsyncMock(side_effect=Exception("API Error"))

        # Should not raise, continues to handler
        await middleware(handler, message, data)

        handler.assert_called_once()


@pytest.mark.asyncio
async def test_reset_session_on_menu_middleware():
    """Test reset session middleware."""
    middleware = ResetSessionOnMenuMiddleware()

    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 123456789
    message.text = "Смотреть анкеты"

    handler = AsyncMock()
    data = {}

    with patch("bot.middlewares.activity_and_session.user_sessions") as mock_sessions:
        mock_sessions.pop = MagicMock()

        await middleware(handler, message, data)

        handler.assert_called_once()


@pytest.mark.asyncio
async def test_user_activity_middleware_no_user():
    """Test middleware when event has no user."""
    middleware = UserActivityMiddleware()

    event = MagicMock()
    event.from_user = None

    handler = AsyncMock()
    data = {}

    await middleware(handler, event, data)

    handler.assert_called_once()
