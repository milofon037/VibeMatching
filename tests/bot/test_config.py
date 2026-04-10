"""Tests for bot configuration."""

import pytest
import os
from unittest.mock import patch

from bot.config import BotSettings


class TestBotSettings:
    """Tests for bot settings configuration."""
    
    def test_telegram_bot_token_from_env(self):
        """Test reading bot token from environment."""
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "test_token_123"}):
            settings = BotSettings()
            assert settings.telegram_bot_token == "test_token_123"
    
    def test_telegram_bot_token_default(self):
        """Test default bot token."""
        with patch.dict(os.environ, {}, clear=True):
            settings = BotSettings()
            assert settings.telegram_bot_token == ""
    
    def test_backend_url_from_env(self):
        """Test reading backend URL from environment."""
        with patch.dict(os.environ, {"BOT_BACKEND_URL": "http://api.example.com/api/v1"}):
            settings = BotSettings()
            assert settings.backend_base_url == "http://api.example.com/api/v1"
    
    def test_backend_url_default(self):
        """Test default backend URL."""
        with patch.dict(os.environ, {}, clear=True):
            settings = BotSettings()
            assert settings.backend_base_url == "http://localhost:8000/api/v1"
    
    def test_both_settings_configured(self):
        """Test both settings configured."""
        env_vars = {
            "TELEGRAM_BOT_TOKEN": "token_xyz",
            "BOT_BACKEND_URL": "http://prod.api.com/api/v1"
        }
        with patch.dict(os.environ, env_vars):
            settings = BotSettings()
            assert settings.telegram_bot_token == "token_xyz"
            assert settings.backend_base_url == "http://prod.api.com/api/v1"
