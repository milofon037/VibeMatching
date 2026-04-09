from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards.inline import search_mode_inline_keyboard
from bot.services.common_service import common_service
from bot.services.feed_service import feed_service
from bot.services.profile_service import profile_service
from bot.utils.formatters import build_referral_link


class MenuService:
    async def on_create_profile(self, message: Message, state: FSMContext) -> None:
        await profile_service.start_create_profile(message, state)

    async def on_watch_feed(self, message: Message) -> None:
        if not await common_service.ensure_profile_exists(message):
            return
        await feed_service.show_feed_card(message, message.from_user.id)

    async def on_my_profile(self, message: Message) -> None:
        await profile_service.show_my_profile(message)

    async def on_rating(self, message: Message) -> None:
        await message.answer(
            "⭐ Твой рейтинг: 125\n\n"
            "+20 за лайки\n"
            "+30 за метчи\n"
            "+50 за заполненность анкеты\n"
            "-10 штрафы\n\n"
            "⏳ Временные баллы: 40\n"
            "Сгорят через 3 дня"
        )
        await common_service.show_main_menu(message)

    async def on_change_search_mode(self, message: Message) -> None:
        if not await common_service.ensure_profile_exists(message):
            return
        await message.answer("Выбери режим поиска:", reply_markup=search_mode_inline_keyboard())

    async def on_incoming_likes(self, message: Message) -> None:
        if not await common_service.ensure_profile_exists(message):
            return
        await feed_service.show_incoming_likes(message, message.from_user.id)

    async def on_outgoing_likes(self, message: Message) -> None:
        if not await common_service.ensure_profile_exists(message):
            return
        await feed_service.show_outgoing_likes(message, message.from_user.id)

    async def on_matches(self, message: Message) -> None:
        if not await common_service.ensure_profile_exists(message):
            return
        await feed_service.send_matches_feed(message, message.from_user.id)

    async def on_referral_link(self, message: Message) -> None:
        telegram_id = message.from_user.id
        await message.answer(f"🔗 Твоя ссылка для приглашений:\n\n{build_referral_link(telegram_id)}")
        await common_service.show_main_menu(message)


menu_service = MenuService()
