"""Tests for bot menu handler."""

from unittest.mock import AsyncMock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.menu import on_create_profile, on_my_profile, on_watch_feed


@pytest.mark.asyncio
async def test_on_create_profile(telegram_message: Message):
    """Test create profile button handler."""
    state = AsyncMock(spec=FSMContext)

    with patch("bot.handlers.menu.menu_service") as mock_service:
        mock_service.on_create_profile = AsyncMock()

        await on_create_profile(telegram_message, state)

        mock_service.on_create_profile.assert_called_once()


@pytest.mark.asyncio
async def test_on_watch_feed(telegram_message: Message):
    """Test watch feed button handler."""
    with patch("bot.handlers.menu.menu_service") as mock_service:
        mock_service.on_watch_feed = AsyncMock()

        await on_watch_feed(telegram_message)

        mock_service.on_watch_feed.assert_called_once()


@pytest.mark.asyncio
async def test_on_my_profile(telegram_message: Message):
    """Test my profile button handler."""
    with patch("bot.handlers.menu.menu_service") as mock_service:
        mock_service.on_my_profile = AsyncMock()

        await on_my_profile(telegram_message)

        mock_service.on_my_profile.assert_called_once()
