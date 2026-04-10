"""Extended tests for bot profile handler."""

import pytest
from unittest.mock import AsyncMock, patch
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.handlers.profile import (
    create_profile_name, create_profile_age, create_profile_city,
    create_profile_bio, handle_create_profile_photo
)
from bot.states.profile import CreateProfileState


@pytest.mark.asyncio
async def test_create_profile_name(telegram_message: Message):
    """Test profile name creation handler."""
    state = AsyncMock(spec=FSMContext)
    
    with patch("bot.handlers.profile.profile_service") as mock_service:
        mock_service.handle_create_profile_name = AsyncMock()
        
        await create_profile_name(telegram_message, state)
        
        mock_service.handle_create_profile_name.assert_called_once()


@pytest.mark.asyncio
async def test_create_profile_age(telegram_message: Message):
    """Test profile age creation handler."""
    state = AsyncMock(spec=FSMContext)
    
    with patch("bot.handlers.profile.profile_service") as mock_service:
        mock_service.handle_create_profile_age = AsyncMock()
        
        await create_profile_age(telegram_message, state)
        
        mock_service.handle_create_profile_age.assert_called_once()


@pytest.mark.asyncio
async def test_create_profile_city(telegram_message: Message):
    """Test profile city creation handler."""
    state = AsyncMock(spec=FSMContext)
    
    with patch("bot.handlers.profile.profile_service") as mock_service:
        mock_service.handle_create_profile_city = AsyncMock()
        
        await create_profile_city(telegram_message, state)
        
        mock_service.handle_create_profile_city.assert_called_once()


@pytest.mark.asyncio
async def test_handle_create_profile_photo(telegram_message: Message):
    """Test profile photo upload handler."""
    state = AsyncMock(spec=FSMContext)
    
    with patch("bot.handlers.profile.profile_service") as mock_service:
        mock_service.handle_photo_upload = AsyncMock()
        
        await handle_create_profile_photo(telegram_message, state)
        
        mock_service.handle_photo_upload.assert_called_once()
