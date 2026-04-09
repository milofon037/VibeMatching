from __future__ import annotations

from typing import Any

from aiogram.types import Message

from bot.keyboards.reply import main_menu_keyboard, no_profile_menu_keyboard
from bot.utils.context import api_client


class CommonService:
    async def show_main_menu(self, message: Message) -> None:
        await message.answer("Главное меню:", reply_markup=main_menu_keyboard())

    async def show_no_profile_screen(self, message: Message) -> None:
        await message.answer("Привет! Давай начнем искать твой vibem?)", reply_markup=no_profile_menu_keyboard())

    async def get_my_profile(self, telegram_id: int) -> dict[str, Any] | None:
        status_code, payload = await api_client.get_profile_me(telegram_id)
        if status_code != 200 or not isinstance(payload, dict):
            return None
        return payload

    async def ensure_profile_exists(self, message: Message) -> bool:
        profile = await self.get_my_profile(message.from_user.id)
        if profile:
            return True
        await self.show_no_profile_screen(message)
        return False


common_service = CommonService()
