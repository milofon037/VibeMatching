"""Tests for bot profile handler."""

import pytest
from unittest.mock import AsyncMock, patch
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.handlers.profile import (
    create_profile_name,
    create_profile_age,
    create_profile_city,
    create_profile_bio,
)


@pytest.mark.asyncio
async def test_create_profile_name(telegram_message: Message):
    """Test profile creation - name step."""
    state = AsyncMock(spec=FSMContext)
    
    with patch("bot.handlers.profile.profile_service") as mock_service:
        mock_service.handle_create_profile_name = AsyncMock()
        
        await create_profile_name(telegram_message, state)
        
        mock_service.handle_create_profile_name.assert_called_once()


@pytest.mark.asyncio
async def test_create_profile_age(telegram_message: Message):
    """Test profile creation - age step."""
    state = AsyncMock(spec=FSMContext)
    
    with patch("bot.handlers.profile.profile_service") as mock_service:
        mock_service.handle_create_profile_age = AsyncMock()
        
        await create_profile_age(telegram_message, state)
        
        mock_service.handle_create_profile_age.assert_called_once()


@pytest.mark.asyncio
async def test_create_profile_city(telegram_message: Message):
    """Test profile creation - city step."""
    state = AsyncMock(spec=FSMContext)
    
    with patch("bot.handlers.profile.profile_service") as mock_service:
        mock_service.handle_create_profile_city = AsyncMock()
        
        await create_profile_city(telegram_message, state)
        
        mock_service.handle_create_profile_city.assert_called_once()


@pytest.mark.asyncio
async def test_create_profile_bio(telegram_message: Message):
    """Test profile creation - bio step."""
    state = AsyncMock(spec=FSMContext)
    
    with patch("bot.handlers.profile.profile_service") as mock_service:
        mock_service.handle_create_profile_bio = AsyncMock()
        
        await create_profile_bio(telegram_message, state)
        
        mock_service.handle_create_profile_bio.assert_called_once()
