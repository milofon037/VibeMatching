"""Bot test fixtures and configuration."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram import Bot
from aiogram.types import Chat, Message, User, Update

from bot.services.api_client import BackendClient


@pytest.fixture
def telegram_user() -> User:
    """Create a test Telegram user."""
    return User(
        id=123456789,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="testuser",
    )


@pytest.fixture
def telegram_chat(telegram_user: User) -> Chat:
    """Create a test Telegram chat."""
    return Chat(
        id=telegram_user.id,
        type="private",
        title=None,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
    )


@pytest.fixture
def telegram_message(telegram_user: User, telegram_chat: Chat) -> Message:
    """Create a test Telegram message."""
    return Message(
        message_id=1,
        date=1234567890,
        chat=telegram_chat,
        from_user=telegram_user,
        text="/start",
    )


@pytest.fixture
def telegram_update(telegram_message: Message) -> Update:
    """Create a test Telegram update."""
    return Update(
        update_id=1,
        message=telegram_message,
    )


@pytest.fixture
def mock_bot() -> AsyncMock:
    """Create a mock Telegram bot."""
    bot = AsyncMock(spec=Bot)
    bot.session = AsyncMock()
    return bot


@pytest.fixture
def backend_client() -> BackendClient:
    """Create a test backend client."""
    return BackendClient(base_url="http://localhost:8000/api/v1")


@pytest.fixture
def mock_backend_client() -> AsyncMock:
    """Create a mock backend client."""
    client = AsyncMock(spec=BackendClient)
    return client


@pytest.fixture
def mock_httpx() -> MagicMock:
    """Create a mock httpx client."""
    with patch("httpx.AsyncClient") as mock:
        yield mock
