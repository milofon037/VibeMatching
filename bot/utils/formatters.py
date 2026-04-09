from __future__ import annotations

from typing import Any


def format_profile_card(profile: dict[str, Any]) -> str:
    city = profile.get("city") or "-"
    name = profile.get("name") or "-"
    age = profile.get("age") or "-"
    interests = profile.get("interests") or "-"
    description = profile.get("bio") or "-"
    return f"{city}, {name}, {age}\nИнтересы: {interests}\n\n{description}"


def extract_error_message(payload: dict[str, Any] | Any) -> str:
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str):
                return message
    return "Не удалось выполнить запрос."


def build_referral_link(telegram_id: int) -> str:
    return f"https://t.me/urvibem_bot?start=ref_{telegram_id}"
