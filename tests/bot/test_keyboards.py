"""Tests for bot keyboards."""

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup

from bot.keyboards.inline import (
    complaint_reason_keyboard,
    edit_gender_keyboard,
    feed_actions_keyboard,
    my_profile_edit_keyboard,
    search_mode_inline_keyboard,
)
from bot.keyboards.reply import main_menu_keyboard, next_or_exit_keyboard, no_profile_menu_keyboard


def test_main_menu_keyboard():
    """Test main menu keyboard generation."""
    keyboard = main_menu_keyboard()

    assert isinstance(keyboard, ReplyKeyboardMarkup)
    assert keyboard.keyboard is not None
    assert len(keyboard.keyboard) > 0

    # Check that buttons have appropriate labels
    buttons = [btn.text for row in keyboard.keyboard for btn in row]
    assert len(buttons) > 0
    assert "Смотреть анкеты" in buttons
    assert "Метчи" in buttons


def test_no_profile_menu_keyboard():
    """Test no profile menu keyboard generation."""
    keyboard = no_profile_menu_keyboard()

    assert isinstance(keyboard, ReplyKeyboardMarkup)
    assert keyboard.keyboard is not None

    buttons = [btn.text for row in keyboard.keyboard for btn in row]
    assert "Создать анкету" in buttons


def test_next_or_exit_keyboard():
    """Test next or exit keyboard."""
    keyboard = next_or_exit_keyboard()

    assert isinstance(keyboard, ReplyKeyboardMarkup)
    assert keyboard.keyboard is not None

    buttons = [btn.text for row in keyboard.keyboard for btn in row]
    assert "Следующая" in buttons
    assert "Выйти" in buttons


def test_edit_gender_keyboard():
    """Test edit gender inline keyboard."""
    keyboard = edit_gender_keyboard()

    assert isinstance(keyboard, InlineKeyboardMarkup)
    assert keyboard.inline_keyboard is not None
    buttons = [btn for row in keyboard.inline_keyboard for btn in row]
    assert len(buttons) == 2


def test_search_mode_inline_keyboard():
    """Test search mode selection keyboard."""
    keyboard = search_mode_inline_keyboard()

    assert isinstance(keyboard, InlineKeyboardMarkup)
    assert keyboard.inline_keyboard is not None

    buttons = [btn for row in keyboard.inline_keyboard for btn in row]
    assert len(buttons) == 2
    assert any("Только мой город" in btn.text for btn in buttons)
    assert any("Все анкеты" in btn.text for btn in buttons)


def test_feed_actions_keyboard():
    """Test feed actions keyboard."""
    keyboard = feed_actions_keyboard(profile_id=123)

    assert isinstance(keyboard, InlineKeyboardMarkup)
    buttons = [btn for row in keyboard.inline_keyboard for btn in row]

    texts = [btn.text for btn in buttons]
    assert "❤️ Лайк" in texts
    assert "⏭ Скип" in texts
    assert "🚨 Жалоба" in texts


def test_complaint_reason_keyboard():
    """Test complaint reason keyboard."""
    keyboard = complaint_reason_keyboard(profile_id=456)

    assert isinstance(keyboard, InlineKeyboardMarkup)
    buttons = [btn for row in keyboard.inline_keyboard for btn in row]

    texts = [btn.text for btn in buttons]
    assert "Спам" in texts
    assert "Фейк" in texts


def test_my_profile_edit_keyboard():
    """Test my profile edit keyboard."""
    keyboard = my_profile_edit_keyboard()

    assert isinstance(keyboard, InlineKeyboardMarkup)
    buttons = [btn for row in keyboard.inline_keyboard for btn in row]

    texts = [btn.text for btn in buttons]
    assert "Изменить имя" in texts
    assert "Изменить возраст" in texts
    assert "Изменить пол" in texts
