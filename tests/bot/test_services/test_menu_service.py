"""Tests for bot menu service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.services.menu_service import menu_service


@pytest.mark.asyncio
async def test_menu_service_on_create_profile(telegram_message: Message):
    """Test create profile action."""
    state = AsyncMock(spec=FSMContext)
    
    with patch("bot.services.menu_service.profile_service") as mock_service:
        mock_service.start_create_profile = AsyncMock()
        
        await menu_service.on_create_profile(telegram_message, state)
        
        mock_service.start_create_profile.assert_called_once()


@pytest.mark.asyncio
async def test_menu_service_on_watch_feed(telegram_message: Message):
    """Test watch feed action."""
    with patch("bot.services.menu_service.common_service") as mock_common:
        with patch("bot.services.menu_service.feed_service") as mock_feed:
            mock_common.ensure_profile_exists = AsyncMock(return_value=True)
            mock_feed.show_feed_card = AsyncMock()
            
            await menu_service.on_watch_feed(telegram_message)
            
            mock_common.ensure_profile_exists.assert_called_once()
            mock_feed.show_feed_card.assert_called_once()


@pytest.mark.asyncio
async def test_menu_service_on_my_profile(telegram_message: Message):
    """Test my profile action."""
    with patch("bot.services.menu_service.profile_service") as mock_service:
        mock_service.show_my_profile = AsyncMock()
        
        await menu_service.on_my_profile(telegram_message)
        
        mock_service.show_my_profile.assert_called_once()


@pytest.mark.asyncio
async def test_menu_service_on_incoming_likes(telegram_message: Message):
    """Test incoming likes action."""
    with patch("bot.services.menu_service.common_service") as mock_common:
        with patch("bot.services.menu_service.feed_service") as mock_feed:
            mock_common.ensure_profile_exists = AsyncMock(return_value=True)
            mock_feed.show_incoming_likes = AsyncMock()
            
            await menu_service.on_incoming_likes(telegram_message)
            
            mock_common.ensure_profile_exists.assert_called_once()
            mock_feed.show_incoming_likes.assert_called_once()


@pytest.mark.asyncio
async def test_menu_service_on_matches(telegram_message: Message):
    """Test matches action."""
    with patch("bot.services.menu_service.common_service") as mock_common:
        with patch("bot.services.menu_service.feed_service") as mock_feed:
            mock_common.ensure_profile_exists = AsyncMock(return_value=True)
            mock_feed.send_matches_feed = AsyncMock()
            
            await menu_service.on_matches(telegram_message)
            
            mock_common.ensure_profile_exists.assert_called_once()
            mock_feed.send_matches_feed.assert_called_once()
