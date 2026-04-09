from __future__ import annotations

from io import BytesIO
from typing import Any

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.inline import (
    cancel_edit_keyboard,
    edit_gender_keyboard,
    edit_gender_with_cancel_keyboard,
    my_profile_edit_keyboard,
    preferred_gender_keyboard,
)
from bot.keyboards.reply import main_menu_keyboard, no_profile_menu_keyboard
from bot.services.common_service import common_service
from bot.states.profile import CreateProfileState, UpdateProfileState
from bot.utils.context import api_client, awaiting_photo_upload
from bot.utils.formatters import extract_error_message
from bot.utils.profile_cards import send_profile_card


class ProfileService:
    async def upload_profile_photo(self, telegram_id: int, payload: bytes) -> tuple[int, dict[str, Any]]:
        return await api_client.upload_photo(
            telegram_id=telegram_id,
            payload=payload,
            filename=f"tg_{telegram_id}.jpg",
        )

    async def start_create_profile(self, message: Message, state: FSMContext) -> None:
        telegram_id = message.from_user.id
        if await common_service.get_my_profile(telegram_id):
            await message.answer("Анкета уже создана.")
            await common_service.show_main_menu(message)
            return
        await state.clear()
        await state.set_state(CreateProfileState.name)
        await message.answer("Как тебя зовут?")

    async def show_my_profile(self, message: Message) -> None:
        profile = await common_service.get_my_profile(message.from_user.id)
        if not profile:
            await common_service.show_no_profile_screen(message)
            return
        await send_profile_card(message, profile, reply_markup=my_profile_edit_keyboard())

    async def handle_create_profile_name(self, message: Message, state: FSMContext) -> None:
        await state.update_data(name=(message.text or "").strip())
        await state.set_state(CreateProfileState.age)
        await message.answer("Сколько тебе лет?")

    async def handle_create_profile_age(self, message: Message, state: FSMContext) -> None:
        text = (message.text or "").strip()
        try:
            age = int(text)
        except ValueError:
            await message.answer("Введите возраст числом.")
            return
        if age < 18 or age > 100:
            await message.answer("Возраст должен быть в диапазоне 18-100.")
            return

        await state.update_data(age=age)
        await message.answer("Укажи пол:", reply_markup=edit_gender_keyboard())

    async def handle_create_profile_city(self, message: Message, state: FSMContext) -> None:
        await state.update_data(city=(message.text or "").strip())
        await state.set_state(CreateProfileState.bio)
        await message.answer("Напиши пару слов о себе:")

    async def handle_create_profile_bio(self, message: Message, state: FSMContext) -> None:
        await state.update_data(bio=(message.text or "").strip())
        await state.set_state(CreateProfileState.interests)
        await message.answer("Напиши свои интересы:")

    async def handle_create_profile_interests(self, message: Message, state: FSMContext) -> None:
        await state.update_data(interests=(message.text or "").strip())
        await state.set_state(CreateProfileState.photo)
        awaiting_photo_upload[message.from_user.id] = {"purpose": "create_profile"}
        await message.answer("Отправь фото для анкеты")

    async def handle_waiting_profile_photo_invalid(self, message: Message) -> None:
        await message.answer("Нужно отправить фото (как изображение, не файлом).")

    async def _send_updated_profile_after_change(self, message: Message, telegram_id: int) -> None:
        updated_profile = await common_service.get_my_profile(telegram_id)
        if updated_profile:
            await send_profile_card(message, updated_profile, reply_markup=my_profile_edit_keyboard())

    async def handle_update_profile_value(self, message: Message, state: FSMContext) -> None:
        telegram_id = message.from_user.id
        data = await state.get_data()
        field = data.get("current_field")
        if field not in {"name", "age", "city", "bio", "interests"}:
            return

        text = (message.text or "").strip()
        value: Any = text
        if field == "age":
            try:
                value = int(text)
            except ValueError:
                await message.answer("Возраст должен быть числом.")
                return

        status_code, response = await api_client.update_profile(telegram_id=telegram_id, payload={field: value})
        if status_code != 200:
            await state.clear()
            await message.answer(extract_error_message(response), reply_markup=main_menu_keyboard())
            return

        await state.clear()
        await message.answer("Поле обновлено.", reply_markup=main_menu_keyboard())
        await self._send_updated_profile_after_change(message, telegram_id)

    async def handle_photo_upload(self, message: Message, state: FSMContext) -> None:
        telegram_id = message.from_user.id
        session = awaiting_photo_upload.get(telegram_id)
        if not session:
            return

        buffer = BytesIO()
        await message.bot.download(message.photo[-1], destination=buffer)
        payload = buffer.getvalue()

        purpose = session.get("purpose")
        if purpose == "create_profile":
            data = await state.get_data()
            profile_payload = {
                "name": data.get("name"),
                "age": data.get("age"),
                "gender": data.get("gender"),
                "city": data.get("city"),
                "bio": data.get("bio"),
                "interests": data.get("interests"),
                "preferred_gender": data.get("preferred_gender"),
            }

            status_code, response = await api_client.create_profile(telegram_id=telegram_id, payload=profile_payload)
            if status_code != 200:
                awaiting_photo_upload.pop(telegram_id, None)
                await state.clear()
                await message.answer(extract_error_message(response), reply_markup=no_profile_menu_keyboard())
                return

            await self.upload_profile_photo(telegram_id=telegram_id, payload=payload)
            awaiting_photo_upload.pop(telegram_id, None)
            await state.clear()
            await message.answer("✅ Анкета создана\nЗа заполнение анкеты начислено +X рейтинга", reply_markup=main_menu_keyboard())
            created_profile = await common_service.get_my_profile(telegram_id)
            if created_profile:
                search_mode = created_profile.get("search_city_mode", "local")
                search_mode_human = "Только мой город" if search_mode == "local" else "Все анкеты"
                await message.answer(
                    "Текущий режим поиска: "
                    f"{search_mode_human}.\n"
                    "Изменить его можно кнопкой 'Изменить режим поиска' в главном меню."
                )
                await send_profile_card(message, created_profile, reply_markup=my_profile_edit_keyboard())
            return

        if purpose == "update_photo":
            status_code, response = await self.upload_profile_photo(telegram_id=telegram_id, payload=payload)
            awaiting_photo_upload.pop(telegram_id, None)
            if status_code == 200:
                await message.answer("Фото анкеты обновлено.", reply_markup=main_menu_keyboard())
                await self._send_updated_profile_after_change(message, telegram_id)
                return
            await message.answer(extract_error_message(response), reply_markup=main_menu_keyboard())

    async def handle_answer_callback(self, callback: CallbackQuery, state: FSMContext) -> None:
        if not callback.data:
            return

        _, field, value = callback.data.split(":", maxsplit=2)
        telegram_id = callback.from_user.id
        current_state = await state.get_state()

        if current_state == CreateProfileState.age.state and field == "gender":
            await state.update_data(gender=value)
            await callback.answer("Ок")
            await callback.message.answer("Кто тебе интересен?", reply_markup=preferred_gender_keyboard())
            return

        if field == "preferred_gender":
            await state.update_data(preferred_gender=None if value == "any" else value)
            await callback.answer("Ок")
            await callback.message.answer("Из какого ты города?")
            await state.set_state(CreateProfileState.city)
            return

        if current_state == UpdateProfileState.value.state and field in {"gender", "preferred_gender"}:
            update_value = value if field == "gender" else (None if value == "any" else value)
            status_code, response = await api_client.update_profile(telegram_id=telegram_id, payload={field: update_value})
            if status_code != 200:
                await state.clear()
                await callback.answer("Ошибка")
                await callback.message.answer(extract_error_message(response), reply_markup=main_menu_keyboard())
                return

            await state.clear()
            await callback.answer("Сохранено")
            await callback.message.answer("Поле обновлено.", reply_markup=main_menu_keyboard())
            await self._send_updated_profile_after_change(callback.message, telegram_id)

    async def handle_edit_callback(self, callback: CallbackQuery, state: FSMContext) -> None:
        if not callback.data:
            return

        _, field = callback.data.split(":", maxsplit=1)
        telegram_id = callback.from_user.id

        if field == "cancel":
            awaiting_photo_upload.pop(telegram_id, None)
            await state.clear()
            await callback.answer("Редактирование отменено")
            await callback.message.answer("Изменение поля отменено.", reply_markup=main_menu_keyboard())
            return

        if field == "photo":
            awaiting_photo_upload[telegram_id] = {"purpose": "update_photo"}
            await callback.answer("Ок")
            await callback.message.answer("Отправь новое фото для анкеты", reply_markup=cancel_edit_keyboard())
            return

        await state.clear()
        await state.set_state(UpdateProfileState.value)
        await state.update_data(current_field=field)
        await callback.answer("Ок")

        prompts = {
            "gender": ("Выбери новый пол:", edit_gender_with_cancel_keyboard()),
            "interests": ("Введи новый интерес:", cancel_edit_keyboard()),
            "name": ("Введи новое имя:", cancel_edit_keyboard()),
            "age": ("Введи новый возраст:", cancel_edit_keyboard()),
            "city": ("Введи новый город:", cancel_edit_keyboard()),
            "bio": ("Введи новое описание:", cancel_edit_keyboard()),
        }
        text, markup = prompts.get(field, ("Введи новое значение:", cancel_edit_keyboard()))
        await callback.message.answer(text, reply_markup=markup)


profile_service = ProfileService()
