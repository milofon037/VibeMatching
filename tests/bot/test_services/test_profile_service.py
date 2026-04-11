"""Tests for bot profile service."""

from unittest.mock import AsyncMock, patch

import pytest
from aiogram.types import Message

from bot.services.profile_service import profile_service


@pytest.mark.asyncio
async def test_profile_service_upload_profile_photo():
    """Test uploading profile photo."""
    with patch("bot.services.profile_service.api_client") as mock_api:
        mock_api.upload_photo = AsyncMock(return_value=(200, {"photo_id": 123}))

        result = await profile_service.upload_profile_photo(123456789, b"photo_data")

        assert result[0] == 200
        assert result[1]["photo_id"] == 123
        mock_api.upload_photo.assert_called_once()


@pytest.mark.asyncio
async def test_profile_service_show_my_profile(telegram_message: Message):
    """Test showing personal profile."""
    with patch("bot.services.profile_service.common_service") as mock_service:
        with patch("bot.services.profile_service.send_profile_card") as mock_send:
            mock_service.get_my_profile = AsyncMock(
                return_value={"id": 1, "name": "John", "age": 25}
            )

            await profile_service.show_my_profile(telegram_message)

            mock_service.get_my_profile.assert_called_once()
            mock_send.assert_called_once()
