"""Tests for bot handlers."""

from unittest.mock import AsyncMock, patch

import pytest
from aiogram.types import Message

from bot.handlers.start import cmd_start


@pytest.mark.asyncio
async def test_cmd_start_user_not_registered(telegram_message: Message):
    """Test /start command when user is not registered."""
    with patch("bot.handlers.start.start_flow_service") as mock_service:
        mock_service.handle_start = AsyncMock()

        await cmd_start(telegram_message)

        mock_service.handle_start.assert_called_once_with(telegram_message)


@pytest.mark.asyncio
async def test_cmd_start_user_has_profile(telegram_message: Message):
    """Test /start command when user has profile."""
    with patch("bot.handlers.start.start_flow_service") as mock_service:
        mock_service.handle_start = AsyncMock()

        await cmd_start(telegram_message)

        mock_service.handle_start.assert_called_once_with(telegram_message)
