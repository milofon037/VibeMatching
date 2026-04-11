"""Tests for bot feed handler."""

from unittest.mock import AsyncMock, patch

import pytest
from aiogram.types import CallbackQuery, Message

from bot.handlers.feed import on_feed_action, on_feed_mode, on_nav_action


@pytest.mark.asyncio
async def test_on_nav_action(telegram_message: Message):
    """Test navigation action handler."""
    with patch("bot.handlers.feed.feed_service") as mock_service:
        mock_service.handle_nav_action = AsyncMock()

        await on_nav_action(telegram_message)

        mock_service.handle_nav_action.assert_called_once()


@pytest.mark.asyncio
async def test_on_feed_mode():
    """Test feed mode selection."""
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "feed:mode"

    with patch("bot.handlers.feed.feed_service") as mock_service:
        mock_service.handle_feed_mode = AsyncMock()

        await on_feed_mode(callback)

        mock_service.handle_feed_mode.assert_called_once()


@pytest.mark.asyncio
async def test_on_feed_action():
    """Test feed action callback."""
    callback = AsyncMock(spec=CallbackQuery)
    callback.data = "feed:like:123"

    with patch("bot.handlers.feed.feed_service") as mock_service:
        mock_service.handle_feed_action = AsyncMock()

        await on_feed_action(callback)

        mock_service.handle_feed_action.assert_called_once()
