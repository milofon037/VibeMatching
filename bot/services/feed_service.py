from __future__ import annotations

from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import (
    complaint_reason_keyboard,
    feed_actions_keyboard,
    incoming_like_actions_keyboard,
    search_mode_inline_keyboard,
)
from bot.keyboards.reply import next_or_exit_keyboard
from bot.services.common_service import common_service
from bot.utils.context import api_client, user_sessions
from bot.utils.profile_cards import send_profile_card


class FeedService:
    async def _finish_profiles_session(self, message: Message, telegram_id: int) -> None:
        user_sessions.pop(telegram_id, None)
        await message.answer("Список анкет завершен.")
        await common_service.show_main_menu(message)

    async def _is_match(self, telegram_id: int, profile_id: int) -> bool:
        incoming_code, incoming_payload = await api_client.incoming_likes(
            telegram_id=telegram_id, limit=200
        )
        if incoming_code != 200 or not isinstance(incoming_payload, list):
            return False
        incoming_ids = {profile["id"] for profile in incoming_payload}
        return profile_id in incoming_ids

    async def _show_likes_session(
        self,
        message: Message,
        telegram_id: int,
        incoming: bool,
        limit: int = 20,
    ) -> None:
        mode = "likes_incoming" if incoming else "likes_outgoing"
        empty_message = "Тебя лайкнули: пока пусто." if incoming else "Ты лайкал: пока пусто."
        fetch = api_client.incoming_likes if incoming else api_client.outgoing_likes

        status_code, payload = await fetch(telegram_id=telegram_id, limit=limit)
        if status_code != 200 or not isinstance(payload, list):
            await message.answer("Не удалось получить список лайков.")
            return
        if not payload:
            await message.answer(empty_message)
            await common_service.show_main_menu(message)
            return

        await self.start_session(telegram_id, mode, payload)
        await self.send_current_session_profile(message, telegram_id)

    async def start_session(self, telegram_id: int, mode: str, profiles: list[dict]) -> None:
        user_sessions[telegram_id] = {"mode": mode, "profiles": profiles, "index": 0}

    async def send_current_session_profile(self, message: Message, telegram_id: int) -> None:
        session = user_sessions.get(telegram_id)
        if not session:
            await common_service.show_main_menu(message)
            return

        profiles = session["profiles"]
        index = session["index"]
        mode = session["mode"]

        if index >= len(profiles):
            await self._finish_profiles_session(message, telegram_id)
            return

        profile = profiles[index]

        if mode == "likes_incoming":
            await send_profile_card(
                message,
                profile,
                title=f"Тебя лайкнули ({index + 1}/{len(profiles)}):",
                reply_markup=incoming_like_actions_keyboard(int(profile["id"])),
            )
            return

        if mode == "likes_outgoing":
            await send_profile_card(
                message, profile, title=f"Ты лайкал ({index + 1}/{len(profiles)}):"
            )
            if index >= len(profiles) - 1:
                await self._finish_profiles_session(message, telegram_id)
                return
            await message.answer("Выберите действие:", reply_markup=next_or_exit_keyboard())
            return

        if mode == "matches":
            await send_profile_card(
                message, profile, title=f"Твои метчи ({index + 1}/{len(profiles)}):"
            )
            await message.answer("Выберите действие:", reply_markup=next_or_exit_keyboard())

    async def show_feed_card(self, message: Message, telegram_id: int) -> None:
        status_code, payload = await api_client.feed(telegram_id=telegram_id, limit=1)
        if status_code != 200:
            await message.answer("Не удалось получить ленту. Попробуйте позже.")
            return

        if not isinstance(payload, list) or not payload:
            await message.answer("Анкеты закончились. Попробуйте позже.")
            await common_service.show_main_menu(message)
            return

        await send_profile_card(
            message,
            payload[0],
            reply_markup=feed_actions_keyboard(int(payload[0]["id"])),
        )

    async def send_matches_feed(self, message: Message, telegram_id: int) -> None:
        status_code, payload = await api_client.get_matches(telegram_id=telegram_id)
        if status_code != 200 or not isinstance(payload, list):
            await message.answer("Не удалось получить метчи.")
            return
        if not payload:
            await message.answer("Метчей пока нет.")
            await common_service.show_main_menu(message)
            return

        outgoing_code, outgoing = await api_client.outgoing_likes(
            telegram_id=telegram_id, limit=100
        )
        incoming_code, incoming = await api_client.incoming_likes(
            telegram_id=telegram_id, limit=100
        )
        if (
            outgoing_code != 200
            or incoming_code != 200
            or not isinstance(outgoing, list)
            or not isinstance(incoming, list)
        ):
            await message.answer("Не удалось подготовить ленту метчей.")
            return

        incoming_ids = {profile["id"] for profile in incoming}
        matched_profiles = [profile for profile in outgoing if profile.get("id") in incoming_ids]
        if not matched_profiles:
            await message.answer("Метчей пока нет.")
            await common_service.show_main_menu(message)
            return

        await self.start_session(telegram_id, "matches", matched_profiles)
        await self.send_current_session_profile(message, telegram_id)

    async def show_incoming_likes(self, message: Message, telegram_id: int) -> None:
        await self._show_likes_session(message, telegram_id, incoming=True)

    async def show_outgoing_likes(self, message: Message, telegram_id: int) -> None:
        await self._show_likes_session(message, telegram_id, incoming=False)

    async def handle_nav_action(self, message: Message) -> None:
        telegram_id = message.from_user.id
        action = message.text or ""
        session = user_sessions.get(telegram_id)
        if not session:
            await common_service.show_main_menu(message)
            return

        if session["mode"] == "likes_incoming":
            await message.answer("Для этого списка используй кнопки под анкетой.")
            return

        if action == "Выйти":
            user_sessions.pop(telegram_id, None)
            await common_service.show_main_menu(message)
            return

        if action == "Следующая":
            session["index"] += 1
            await self.send_current_session_profile(message, telegram_id)

    async def handle_feed_mode(self, callback: CallbackQuery) -> None:
        await callback.answer("Ок")
        await callback.message.answer(
            "Выбери режим поиска:", reply_markup=search_mode_inline_keyboard()
        )

    async def handle_feed_action(self, callback: CallbackQuery) -> None:
        if not callback.data:
            return

        _, action, profile_id_raw = callback.data.split(":", maxsplit=2)
        telegram_id = callback.from_user.id
        profile_id = int(profile_id_raw)

        if action == "like":
            is_match = await self._is_match(telegram_id=telegram_id, profile_id=profile_id)

            status_code, _ = await api_client.swipe_like(
                telegram_id=telegram_id, to_profile_id=profile_id
            )
            if status_code == 200:
                try:
                    await callback.message.edit_reply_markup(reply_markup=None)
                except Exception:
                    pass
                await callback.answer("Ок")
                await callback.message.answer("🎉 У вас матч!" if is_match else "❤️ Лайк отправлен")
                await self.show_feed_card(callback.message, telegram_id)
                return

        if action == "skip":
            status_code, _ = await api_client.swipe_skip(
                telegram_id=telegram_id, to_profile_id=profile_id
            )
            if status_code == 200:
                try:
                    await callback.message.edit_reply_markup(reply_markup=None)
                except Exception:
                    pass
                await callback.answer("Ок")
                await self.show_feed_card(callback.message, telegram_id)
                return

        if action == "complaint":
            await callback.answer("Ок")
            await callback.message.answer(
                "Укажи причину жалобы:", reply_markup=complaint_reason_keyboard(profile_id)
            )
            return

        await callback.answer("Ошибка действия", show_alert=True)

    async def handle_mode_change(self, callback: CallbackQuery) -> None:
        if not callback.data:
            return

        _, mode = callback.data.split(":", maxsplit=1)
        telegram_id = callback.from_user.id
        status_code, _ = await api_client.update_search_mode(
            telegram_id=telegram_id, search_city_mode=mode
        )
        if status_code == 200:
            await callback.answer("Режим обновлен")
            human_mode = "Только мой город" if mode == "local" else "Все анкеты"
            await callback.message.answer(f"Режим поиска: {human_mode}")
            return

        await callback.answer("Ошибка")

    async def handle_complaint_reason(self, callback: CallbackQuery) -> None:
        if not callback.data:
            return

        await callback.answer("Жалоба отправлена")
        await callback.message.answer("Жалоба принята и отправлена на модерацию.")
        await self.show_feed_card(callback.message, callback.from_user.id)

    async def handle_incoming_like_action(self, callback: CallbackQuery) -> None:
        if not callback.data:
            return

        _, action, profile_id_raw = callback.data.split(":", maxsplit=2)
        telegram_id = callback.from_user.id
        profile_id = int(profile_id_raw)

        if action == "like":
            status_code, _ = await api_client.swipe_like(
                telegram_id=telegram_id, to_profile_id=profile_id
            )
            if status_code == 200:
                await callback.answer("Ок")
                await callback.message.answer("🎉 У вас матч!")
        elif action == "skip":
            status_code, _ = await api_client.swipe_skip(
                telegram_id=telegram_id, to_profile_id=profile_id
            )
            if status_code == 200:
                await callback.answer("Ок")
                await callback.message.answer("Анкета пропущена")

        session = user_sessions.get(telegram_id)
        if session and session.get("mode") == "likes_incoming":
            session["index"] += 1
            await self.send_current_session_profile(callback.message, telegram_id)


feed_service = FeedService()
