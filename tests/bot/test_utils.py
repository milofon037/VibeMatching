"""Tests for bot utils and formatters."""

import pytest

from bot.utils.formatters import format_profile_card, extract_error_message, build_referral_link


class TestProfileCardFormatter:
    """Tests for profile card formatting."""
    
    def test_format_profile_card_complete(self):
        """Test formatting profile with all fields."""
        profile = {
            "name": "John",
            "age": 25,
            "city": "Moscow",
            "interests": "Music, Sports",
            "bio": "Software engineer"
        }
        
        result = format_profile_card(profile)
        
        assert "Moscow" in result
        assert "John" in result
        assert "25" in result
        assert "Music, Sports" in result
        assert "Software engineer" in result
    
    def test_format_profile_card_missing_fields(self):
        """Test formatting profile with missing fields."""
        profile = {
            "name": "John",
            "age": 25,
            "city": None
        }
        
        result = format_profile_card(profile)
        
        assert "-" in result  # Missing city should be replaced with "-"
        assert "John" in result
        assert "25" in result
    
    def test_format_profile_card_empty(self):
        """Test formatting empty profile."""
        profile = {}
        
        result = format_profile_card(profile)
        
        assert "-" in result


class TestErrorMessageExtractor:
    """Tests for error message extraction."""
    
    def test_extract_error_message_nested_dict(self):
        """Test extracting error from nested dict."""
        payload = {
            "error": {
                "code": "user_not_found",
                "message": "User not found"
            }
        }
        
        result = extract_error_message(payload)
        
        assert result == "User not found"
    
    def test_extract_error_message_flat_dict(self):
        """Test extracting error from flat dict."""
        payload = {"message": "Some error"}
        
        result = extract_error_message(payload)
        
        assert result == "Не удалось выполнить запрос."  # Returns default for flat dict
    
    def test_extract_error_message_string(self):
        """Test extracting error from string."""
        payload = "Some error string"
        
        result = extract_error_message(payload)
        
        assert result == "Не удалось выполнить запрос."
    
    def test_extract_error_message_default(self):
        """Test default error message."""
        payload = {}
        
        result = extract_error_message(payload)
        
        assert result == "Не удалось выполнить запрос."


class TestReferralLinkBuilder:
    """Tests for referral link building."""
    
    def test_build_referral_link(self):
        """Test building referral link."""
        telegram_id = 123456789
        
        result = build_referral_link(telegram_id)
        
        assert result == "https://t.me/urvibem_bot?start=ref_123456789"
    
    def test_build_referral_link_different_id(self):
        """Test building referral link with different ID."""
        telegram_id = 999
        
        result = build_referral_link(telegram_id)
        
        assert "999" in result
        assert result.startswith("https://t.me/urvibem_bot?start=ref_")
