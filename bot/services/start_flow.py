from aiogram.types import Message

from bot.keyboards.reply import main_menu_keyboard, no_profile_menu_keyboard
from bot.utils.context import api_client


class StartFlowService:
    async def handle_start(self, message: Message) -> None:
        telegram_id = message.from_user.id
        status_code, _ = await api_client.register_user(telegram_id=telegram_id)
        if status_code not in (200, 201):
            await message.answer("Ошибка регистрации. Попробуйте позже.")
            return

        profile_status, _ = await api_client.get_profile_me(telegram_id=telegram_id)
        if profile_status == 200:
            await message.answer("Главное меню:", reply_markup=main_menu_keyboard())
            return

        await message.answer("Привет! Давай начнем искать твой vibem?)", reply_markup=no_profile_menu_keyboard())


start_flow_service = StartFlowService()
