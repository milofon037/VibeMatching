"""Tests for bot common service and start flow."""

from unittest.mock import AsyncMock, patch

import pytest
from aiogram.types import Message

from bot.services.common_service import common_service
from bot.services.start_flow import start_flow_service


@pytest.mark.asyncio
async def test_common_service_get_my_profile():
    """Test getting user profile."""
    with patch("bot.services.common_service.api_client") as mock_api:
        mock_api.get_profile_me = AsyncMock(return_value=(200, {"name": "John", "id": 1}))

        result = await common_service.get_my_profile(123456789)

        assert result["id"] == 1
        assert result["name"] == "John"
        mock_api.get_profile_me.assert_called_once()


@pytest.mark.asyncio
async def test_common_service_get_my_profile_not_found():
    """Test get profile when not found."""
    with patch("bot.services.common_service.api_client") as mock_api:
        mock_api.get_profile_me = AsyncMock(return_value=(404, {}))

        result = await common_service.get_my_profile(123456789)

        assert result is None


@pytest.mark.asyncio
async def test_common_service_ensure_profile_exists(telegram_message: Message):
    """Test ensure profile exists."""
    with patch("bot.services.common_service.api_client") as mock_api:
        mock_api.get_profile_me = AsyncMock(return_value=(200, {"id": 1}))

        result = await common_service.ensure_profile_exists(telegram_message)

        assert result is True


@pytest.mark.asyncio
async def test_start_flow_service_handle_start_new_user():
    """Test start flow for new user."""
    # Use MagicMock instead of real Message to allow method mocking
    mock_message = AsyncMock()
    with patch("bot.services.start_flow.api_client") as mock_api:
        mock_api.register_user = AsyncMock(return_value=(200, {}))
        mock_api.get_profile_me = AsyncMock(return_value=(404, {}))

        await start_flow_service.handle_start(mock_message)

        mock_api.register_user.assert_called_once()
        mock_api.get_profile_me.assert_called_once()


@pytest.mark.asyncio
async def test_start_flow_service_handle_start_existing_user():
    """Test start flow for existing user with profile."""
    # Use MagicMock instead of real Message to allow method mocking
    mock_message = AsyncMock()
    with patch("bot.services.start_flow.api_client") as mock_api:
        mock_api.register_user = AsyncMock(return_value=(200, {}))
        mock_api.get_profile_me = AsyncMock(return_value=(200, {"name": "John"}))

        await start_flow_service.handle_start(mock_message)

        mock_api.register_user.assert_called_once()
