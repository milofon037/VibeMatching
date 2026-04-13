"""Tests for bot API client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.services.api_client import BackendClient


@pytest.mark.asyncio
async def test_register_user_success():
    """Test successful user registration."""
    client = BackendClient(base_url="http://localhost:8000/api/v1")

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "telegram_id": 123456789}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        status_code, data = await client.register_user(telegram_id=123456789)

        assert status_code == 200
        assert data["telegram_id"] == 123456789
        mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_get_profile_me_success():
    """Test getting user profile."""
    client = BackendClient(base_url="http://localhost:8000/api/v1")

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "user_id": 1,
            "name": "John",
            "age": 25,
            "gender": "male",
            "city": "Moscow",
        }

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        status_code, data = await client.get_profile_me(telegram_id=123456789)

        assert status_code == 200
        assert data["name"] == "John"
        mock_client.get.assert_called_once()


@pytest.mark.asyncio
async def test_get_profile_me_not_found():
    """Test getting profile when it doesn't exist."""
    client = BackendClient(base_url="http://localhost:8000/api/v1")

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Profile not found"}

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        status_code, data = await client.get_profile_me(telegram_id=123456789)

        assert status_code == 404


@pytest.mark.asyncio
async def test_create_profile_success():
    """Test profile creation."""
    client = BackendClient(base_url="http://localhost:8000/api/v1")

    profile_data = {"name": "John", "age": 25, "gender": "male", "city": "Moscow"}

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, **profile_data}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        status_code, data = await client.create_profile(telegram_id=123456789, payload=profile_data)

        assert status_code == 200
        assert data["name"] == "John"


@pytest.mark.asyncio
async def test_update_activity_success():
    """Test updating user activity."""
    client = BackendClient(base_url="http://localhost:8000/api/v1")

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"user_id": 1, "last_active_at": "2026-04-10T16:00:00"}

        mock_client = AsyncMock()
        mock_client.patch = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        status_code, data = await client.update_activity(telegram_id=123456789)

        assert status_code == 200
        assert data["user_id"] == 1


@pytest.mark.asyncio
async def test_backend_client_headers():
    """Test that correct headers are sent."""
    client = BackendClient(base_url="http://localhost:8000/api/v1")

    headers = client._headers(telegram_id=123456789)

    assert headers["X-Telegram-Id"] == "123456789"


@pytest.mark.asyncio
async def test_backend_client_base_url_normalization():
    """Test that base URL is normalized."""
    client = BackendClient(base_url="http://localhost:8000/api/v1/")

    assert client.base_url == "http://localhost:8000/api/v1"
