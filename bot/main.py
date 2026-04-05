import asyncio
import logging
from collections import defaultdict
from io import BytesIO
from typing import Any

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot.backend_client import BackendClient
from bot.config import settings
from bot.keyboards import (
    gender_keyboard,
    likes_navigation_keyboard,
    main_menu_keyboard,
    no_profile_menu_keyboard,
    profile_actions_keyboard,
    profile_edit_field_keyboard,
    profile_edit_inline_keyboard,
    search_mode_keyboard,
    yes_no_skip_keyboard,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

backend = BackendClient(base_url=settings.backend_base_url)
last_card_by_user: dict[int, int | None] = defaultdict(lambda: None)
awaiting_photo_upload: set[int] = set()
likes_sessions: dict[int, dict[str, Any]] = {}

MENU_ACTIONS = {
    "0. Создать анкету",
    "1. Моя анкета",
    "2. Мой рейтинг",
    "3. Кого я лайкал",
    "4. Кто лайкал меня",
    "5. Мои мэтчи",
    "6. Реферальная ссылка",
    "7. Смотреть анкеты",
}

LIKES_NAV_ACTIONS = {"Следующая", "Выйти"}

ALLOWED_UPDATE_FIELDS = {
    "name",
    "age",
    "city",
    "bio",
    "interests",
    "gender",
    "preferred_gender",
    "preferred_age_min",
    "preferred_age_max",
    "search_city_mode",
}


class CreateProfileState(StatesGroup):
    name = State()
    age = State()
    gender = State()
    city = State()
    bio = State()
    interests = State()
    preferred_gender = State()
    preferred_age_min = State()
    preferred_age_max = State()
    search_mode = State()


class UpdateProfileState(StatesGroup):
    field = State()
    value = State()


def _format_profile_card(profile: dict) -> str:
    interests = profile.get("interests") or "-"
    description = profile.get("bio") or "-"
    city = profile.get("city") or "-"
    name = profile.get("name") or "-"
    age = profile.get("age") or "-"
    return f"{city}, {name}, {age}\nИнтересы: {interests}\n\n{description}"


def _extract_error_message(payload: dict) -> str:
    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str):
            return message
    return "Не удалось выполнить запрос."


async def _get_primary_photo_url(profile_id: int) -> str | None:
    status_code, payload = await backend.get_profile_photos(profile_id=profile_id)
    if status_code != 200 or not isinstance(payload, list) or not payload:
        return None

    photos = sorted(payload, key=lambda photo: photo.get("position", 10_000))
    first_photo = photos[0]
    photo_url = first_photo.get("photo_url")
    if isinstance(photo_url, str) and photo_url:
        return photo_url
    return None


async def _send_profile_card(
    message: Message,
    profile: dict,
    reply_markup=None,
    header: str | None = None,
) -> None:
    caption = _format_profile_card(profile)
    if header:
        caption = f"{header}\n\n{caption}"

    photo_url = await _get_primary_photo_url(profile_id=int(profile["id"]))
    if photo_url:
        try:
            await message.answer_photo(photo=photo_url, caption=caption, reply_markup=reply_markup)
            return
        except Exception:
            logger.warning("failed to send photo for profile_id=%s", profile.get("id"))

    await message.answer(caption, reply_markup=reply_markup)


async def show_main_menu(message: Message) -> None:
    await message.answer("Главное меню:", reply_markup=main_menu_keyboard())


async def show_no_profile_menu(message: Message) -> None:
    await message.answer(
        "Пока у тебя нет анкеты. Доступно только создание анкеты.",
        reply_markup=no_profile_menu_keyboard(),
    )


async def ensure_profile_exists(message: Message) -> bool:
    telegram_id = message.from_user.id
    status_code, _ = await backend.get_profile_me(telegram_id)
    if status_code == 200:
        return True
    await show_no_profile_menu(message)
    return False


def _build_referral_link(telegram_id: int) -> str:
    return f"https://t.me/urvibem_bot?start=ref_{telegram_id}"


async def _prompt_for_update_field(message: Message, field: str) -> None:
    if field == "gender":
        await message.answer("Новое значение для gender:", reply_markup=gender_keyboard())
        return
    if field == "preferred_gender":
        await message.answer("Новое значение для preferred_gender или any:", reply_markup=gender_keyboard(allow_any=True))
        return
    if field == "search_city_mode":
        await message.answer("Новое значение search_city_mode:", reply_markup=search_mode_keyboard())
        return

    await message.answer(
        "Введи новое значение (или 'skip' для очистки optional поля).",
        reply_markup=yes_no_skip_keyboard(),
    )


async def _show_my_profile(message: Message, telegram_id: int) -> None:
    status_code, payload = await backend.get_profile_me(telegram_id)
    if status_code != 200:
        await show_no_profile_menu(message)
        return

    await _send_profile_card(message, payload)
    await message.answer("Редактировать:", reply_markup=profile_edit_inline_keyboard())


async def start_create_profile_flow(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CreateProfileState.name)
    await message.answer("Создание анкеты. Вопрос 1/10: Как тебя зовут?")


async def start_update_profile_flow(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(UpdateProfileState.field)
    await state.update_data(pending_updates={})
    await message.answer(
        "Редактирование анкеты. Какое поле изменить?\n"
        "Когда закончишь, нажми 'done'.",
        reply_markup=profile_edit_field_keyboard(),
    )


async def send_next_feed_card(message: Message, telegram_id: int) -> None:
    logger.info("feed request: telegram_id=%s", telegram_id)
    status_code, payload = await backend.feed(telegram_id=telegram_id, limit=1)
    if status_code != 200:
        await message.answer("Не удалось получить ленту. Попробуйте позже.")
        return

    if not isinstance(payload, list) or len(payload) == 0:
        last_card_by_user[telegram_id] = None
        await message.answer("Анкеты закончились. Попробуйте позже.")
        return

    profile = payload[0]
    last_card_by_user[telegram_id] = int(profile["id"])
    await _send_profile_card(
        message,
        profile,
        reply_markup=profile_actions_keyboard(int(profile["id"])),
    )


async def _send_current_likes_card(message: Message, telegram_id: int) -> None:
    session = likes_sessions.get(telegram_id)
    if not session:
        await show_main_menu(message)
        return

    index = session["index"]
    profiles = session["profiles"]
    if index >= len(profiles):
        likes_sessions.pop(telegram_id, None)
        await message.answer("Список анкет завершен.")
        await show_main_menu(message)
        return

    profile = profiles[index]
    title = session["title"]
    await _send_profile_card(
        message,
        profile,
        header=f"{title} ({index + 1}/{len(profiles)})",
    )
    await message.answer("Выберите действие:", reply_markup=likes_navigation_keyboard())


async def _start_likes_feed(message: Message, telegram_id: int, incoming: bool) -> None:
    if incoming:
        title = "Вас лайкнули"
        status_code, payload = await backend.incoming_likes(telegram_id=telegram_id, limit=20)
    else:
        title = "Вы лайкнули"
        status_code, payload = await backend.outgoing_likes(telegram_id=telegram_id, limit=20)

    if status_code != 200:
        await message.answer("Не удалось получить список лайков. Попробуйте позже.")
        return
    if not isinstance(payload, list) or len(payload) == 0:
        await message.answer(f"{title}: пока пусто.")
        await show_main_menu(message)
        return

    likes_sessions[telegram_id] = {
        "title": title,
        "profiles": payload,
        "index": 0,
    }
    await _send_current_likes_card(message, telegram_id=telegram_id)


async def cmd_start(message: Message) -> None:
    telegram_id = message.from_user.id
    logger.info("/start: telegram_id=%s", telegram_id)

    status_code, _ = await backend.register_user(telegram_id=telegram_id)
    if status_code not in (200, 201):
        await message.answer("Ошибка регистрации. Попробуйте позже.")
        return

    profile_status, _ = await backend.get_profile_me(telegram_id=telegram_id)
    if profile_status == 404:
        await show_no_profile_menu(message)
        return

    await message.answer("С возвращением!")
    await show_main_menu(message)


async def cmd_menu(message: Message) -> None:
    likes_sessions.pop(message.from_user.id, None)
    if await ensure_profile_exists(message):
        await show_main_menu(message)


async def cmd_feed(message: Message) -> None:
    likes_sessions.pop(message.from_user.id, None)
    if not await ensure_profile_exists(message):
        return
    await send_next_feed_card(message, telegram_id=message.from_user.id)


async def cmd_matches(message: Message) -> None:
    likes_sessions.pop(message.from_user.id, None)
    if not await ensure_profile_exists(message):
        return
    telegram_id = message.from_user.id
    logger.info("/matches: telegram_id=%s", telegram_id)
    status_code, payload = await backend.get_matches(telegram_id=telegram_id)
    if status_code != 200:
        await message.answer("Не удалось получить мэтчи.")
        return

    if not isinstance(payload, list) or len(payload) == 0:
        await message.answer("Мэтчей пока нет.")
        return

    lines: list[str] = ["Твои мэтчи:"]
    for match in payload:
        lines.append(
            f"match_id={match['id']} pair=({match['user1_id']},{match['user2_id']}) "
            f"dialog_started={match['dialog_started']}"
        )
    lines.append("Чтобы отметить старт диалога: /start_dialog <match_id>")
    await message.answer("\n".join(lines))


async def cmd_start_dialog(message: Message) -> None:
    likes_sessions.pop(message.from_user.id, None)
    if not await ensure_profile_exists(message):
        return
    telegram_id = message.from_user.id
    logger.info("/start_dialog: telegram_id=%s", telegram_id)
    parts = message.text.split()
    if len(parts) != 2:
        await message.answer("Формат: /start_dialog <match_id>")
        return

    try:
        match_id = int(parts[1])
    except ValueError:
        await message.answer("match_id должен быть числом.")
        return

    status_code, payload = await backend.mark_dialog_started(telegram_id=telegram_id, match_id=match_id)
    if status_code == 200:
        await message.answer(f"Диалог отмечен как начатый для match_id={payload['id']}")
        return
    await message.answer("Не удалось отметить старт диалога.")


async def on_menu_action(message: Message, state: FSMContext) -> None:
    telegram_id = message.from_user.id
    text = message.text or ""
    likes_sessions.pop(telegram_id, None)

    if text == "0. Создать анкету":
        status_code, _ = await backend.get_profile_me(telegram_id)
        if status_code == 200:
            await message.answer("Анкета уже существует. Используй пункт '1. Моя анкета' для редактирования.")
            await show_main_menu(message)
            return
        await start_create_profile_flow(message, state)
        return

    if text == "1. Моя анкета":
        if not await ensure_profile_exists(message):
            return
        await _show_my_profile(message, telegram_id=telegram_id)
        return

    if text == "2. Мой рейтинг":
        await message.answer("Рейтинг будет доступен после реализации этапа 3.")
        await show_main_menu(message)
        return

    if text == "3. Кого я лайкал":
        if not await ensure_profile_exists(message):
            return
        await _start_likes_feed(message, telegram_id=telegram_id, incoming=False)
        return

    if text == "4. Кто лайкал меня":
        if not await ensure_profile_exists(message):
            return
        await _start_likes_feed(message, telegram_id=telegram_id, incoming=True)
        return

    if text == "5. Мои мэтчи":
        await cmd_matches(message)
        await show_main_menu(message)
        return

    if text == "6. Реферальная ссылка":
        await message.answer(f"Твоя реферальная ссылка:\n{_build_referral_link(telegram_id)}")
        await show_main_menu(message)
        return

    if text == "7. Смотреть анкеты":
        if not await ensure_profile_exists(message):
            return
        await send_next_feed_card(message, telegram_id=telegram_id)
        return


async def handle_likes_navigation(message: Message) -> None:
    telegram_id = message.from_user.id
    action = message.text or ""
    session = likes_sessions.get(telegram_id)
    if not session:
        await show_main_menu(message)
        return

    if action == "Выйти":
        likes_sessions.pop(telegram_id, None)
        await show_main_menu(message)
        return

    if action == "Следующая":
        session["index"] += 1
        await _send_current_likes_card(message, telegram_id=telegram_id)
        return


async def create_profile_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await state.set_state(CreateProfileState.age)
    await message.answer("Вопрос 2/10: Сколько тебе лет? (18-100)")


async def create_profile_age(message: Message, state: FSMContext) -> None:
    try:
        age = int(message.text.strip())
    except ValueError:
        await message.answer("Возраст должен быть числом. Повтори, пожалуйста.")
        return
    if age < 18 or age > 100:
        await message.answer("Возраст должен быть в диапазоне 18-100.")
        return
    await state.update_data(age=age)
    await state.set_state(CreateProfileState.gender)
    await message.answer("Вопрос 3/10: Укажи пол.", reply_markup=gender_keyboard())


async def create_profile_gender(message: Message, state: FSMContext) -> None:
    gender = message.text.strip().lower()
    if gender not in {"male", "female", "other"}:
        await message.answer("Выбери вариант кнопкой: male, female, other.", reply_markup=gender_keyboard())
        return
    await state.update_data(gender=gender)
    await state.set_state(CreateProfileState.city)
    await message.answer("Вопрос 4/10: В каком ты городе?")


async def create_profile_city(message: Message, state: FSMContext) -> None:
    await state.update_data(city=message.text.strip())
    await state.set_state(CreateProfileState.bio)
    await message.answer("Вопрос 5/10: Bio (или 'skip').", reply_markup=yes_no_skip_keyboard())


async def create_profile_bio(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    await state.update_data(bio=None if text.lower() == "skip" else text)
    await state.set_state(CreateProfileState.interests)
    await message.answer("Вопрос 6/10: Интересы (или 'skip').", reply_markup=yes_no_skip_keyboard())


async def create_profile_interests(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    await state.update_data(interests=None if text.lower() == "skip" else text)
    await state.set_state(CreateProfileState.preferred_gender)
    await message.answer(
        "Вопрос 7/10: Предпочитаемый пол (male/female/other) или any.",
        reply_markup=gender_keyboard(allow_any=True),
    )


async def create_profile_preferred_gender(message: Message, state: FSMContext) -> None:
    value = message.text.strip().lower()
    if value not in {"male", "female", "other", "any"}:
        await message.answer("Выбери вариант кнопкой.", reply_markup=gender_keyboard(allow_any=True))
        return
    await state.update_data(preferred_gender=None if value == "any" else value)
    await state.set_state(CreateProfileState.preferred_age_min)
    await message.answer("Вопрос 8/10: Минимальный возраст (или 'skip').", reply_markup=yes_no_skip_keyboard())


async def create_profile_preferred_age_min(message: Message, state: FSMContext) -> None:
    text = message.text.strip().lower()
    if text == "skip":
        await state.update_data(preferred_age_min=None)
    else:
        try:
            age_min = int(text)
        except ValueError:
            await message.answer("Введите число или 'skip'.")
            return
        if age_min < 18 or age_min > 100:
            await message.answer("Возраст должен быть в диапазоне 18-100.")
            return
        await state.update_data(preferred_age_min=age_min)

    await state.set_state(CreateProfileState.preferred_age_max)
    await message.answer("Вопрос 9/10: Максимальный возраст (или 'skip').", reply_markup=yes_no_skip_keyboard())


async def create_profile_preferred_age_max(message: Message, state: FSMContext) -> None:
    text = message.text.strip().lower()
    if text == "skip":
        await state.update_data(preferred_age_max=None)
    else:
        try:
            age_max = int(text)
        except ValueError:
            await message.answer("Введите число или 'skip'.")
            return
        if age_max < 18 or age_max > 100:
            await message.answer("Возраст должен быть в диапазоне 18-100.")
            return
        data = await state.get_data()
        age_min = data.get("preferred_age_min")
        if age_min is not None and age_max < age_min:
            await message.answer("Максимальный возраст должен быть >= минимального.")
            return
        await state.update_data(preferred_age_max=age_max)

    await state.set_state(CreateProfileState.search_mode)
    await message.answer("Вопрос 10/10: Режим поиска города (local/global).", reply_markup=search_mode_keyboard())


async def create_profile_finish(message: Message, state: FSMContext) -> None:
    mode = message.text.strip().lower()
    if mode not in {"local", "global"}:
        await message.answer("Выбери local или global.", reply_markup=search_mode_keyboard())
        return

    await state.update_data(search_city_mode=mode)
    payload = await state.get_data()
    telegram_id = message.from_user.id

    create_payload = {
        "name": payload["name"],
        "age": payload["age"],
        "gender": payload["gender"],
        "city": payload["city"],
        "bio": payload.get("bio"),
        "interests": payload.get("interests"),
        "preferred_gender": payload.get("preferred_gender"),
        "preferred_age_min": payload.get("preferred_age_min"),
        "preferred_age_max": payload.get("preferred_age_max"),
    }

    status_code, response = await backend.create_profile(telegram_id=telegram_id, payload=create_payload)
    if status_code != 200:
        await state.clear()
        await message.answer(_extract_error_message(response), reply_markup=no_profile_menu_keyboard())
        return

    if mode == "global":
        await backend.update_search_mode(telegram_id=telegram_id, search_city_mode="global")

    await state.clear()
    await message.answer("Анкета успешно создана.", reply_markup=main_menu_keyboard())


async def update_profile_pick_field(message: Message, state: FSMContext) -> None:
    field = message.text.strip()
    if field == "done":
        data = await state.get_data()
        pending_updates: dict = data.get("pending_updates", {})
        if not pending_updates:
            await state.clear()
            await message.answer("Изменений нет.", reply_markup=main_menu_keyboard())
            return

        telegram_id = message.from_user.id
        update_payload = {k: v for k, v in pending_updates.items() if k != "search_city_mode"}
        if update_payload:
            status_code, response = await backend.update_profile(telegram_id=telegram_id, payload=update_payload)
            if status_code != 200:
                await state.clear()
                await message.answer(_extract_error_message(response), reply_markup=main_menu_keyboard())
                return

        search_mode = pending_updates.get("search_city_mode")
        if search_mode is not None:
            await backend.update_search_mode(telegram_id=telegram_id, search_city_mode=search_mode)

        await state.clear()
        await message.answer("Анкета обновлена.", reply_markup=main_menu_keyboard())
        return

    if field not in ALLOWED_UPDATE_FIELDS:
        await message.answer("Выбери поле кнопкой или 'done'.", reply_markup=profile_edit_field_keyboard())
        return

    await state.update_data(current_field=field)
    await state.set_state(UpdateProfileState.value)
    await _prompt_for_update_field(message, field)


async def update_profile_set_value(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    field = data.get("current_field")
    text = message.text.strip()
    if field not in ALLOWED_UPDATE_FIELDS:
        await state.clear()
        await show_main_menu(message)
        return

    value: Any = text
    if field in {"age", "preferred_age_min", "preferred_age_max"}:
        if text.lower() == "skip" and field in {"preferred_age_min", "preferred_age_max"}:
            value = None
        else:
            try:
                value = int(text)
            except ValueError:
                await message.answer("Введите число.")
                return

    if field == "gender" and text.lower() not in {"male", "female", "other"}:
        await message.answer("Выбери male/female/other.", reply_markup=gender_keyboard())
        return
    if field == "preferred_gender" and text.lower() not in {"male", "female", "other", "any"}:
        await message.answer("Выбери male/female/other/any.", reply_markup=gender_keyboard(allow_any=True))
        return
    if field == "preferred_gender" and text.lower() == "any":
        value = None
    if field == "search_city_mode":
        if text.lower() not in {"local", "global"}:
            await message.answer("Выбери local/global.", reply_markup=search_mode_keyboard())
            return
        value = text.lower()

    if field in {"bio", "interests"} and text.lower() == "skip":
        value = None

    inline_single_update = data.get("inline_single_update", False)
    if inline_single_update:
        telegram_id = message.from_user.id
        if field == "search_city_mode":
            status_code, response = await backend.update_search_mode(telegram_id=telegram_id, search_city_mode=value)
        else:
            status_code, response = await backend.update_profile(telegram_id=telegram_id, payload={field: value})

        if status_code != 200:
            await state.clear()
            await message.answer(_extract_error_message(response), reply_markup=main_menu_keyboard())
            return

        await state.clear()
        await message.answer("Поле обновлено.", reply_markup=main_menu_keyboard())
        await _show_my_profile(message, telegram_id=telegram_id)
        return

    pending_updates = data.get("pending_updates", {})
    pending_updates[field] = value
    await state.update_data(pending_updates=pending_updates)

    await state.set_state(UpdateProfileState.field)
    await message.answer(
        f"Поле '{field}' записано. Выбери следующее поле или 'done'.",
        reply_markup=profile_edit_field_keyboard(),
    )


async def on_edit_field(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.data:
        await callback.answer("Некорректное действие")
        return

    _, field = callback.data.split(":", maxsplit=1)
    if field not in ALLOWED_UPDATE_FIELDS:
        await callback.answer("Некорректное поле", show_alert=True)
        return

    await state.clear()
    await state.set_state(UpdateProfileState.value)
    await state.update_data(current_field=field, inline_single_update=True)
    await callback.answer("Ок")
    await _prompt_for_update_field(callback.message, field)


async def on_card_action(callback: CallbackQuery) -> None:
    if not callback.data:
        await callback.answer("Некорректное действие")
        return

    action, profile_id_raw = callback.data.split(":", maxsplit=1)
    try:
        profile_id = int(profile_id_raw)
    except ValueError:
        await callback.answer("Некорректный profile_id")
        return

    telegram_id = callback.from_user.id
    logger.info("card action: telegram_id=%s action=%s profile_id=%s", telegram_id, action, profile_id)
    if action == "like":
        status_code, _ = await backend.swipe_like(telegram_id=telegram_id, to_profile_id=profile_id)
    elif action == "skip":
        status_code, _ = await backend.swipe_skip(telegram_id=telegram_id, to_profile_id=profile_id)
    else:
        await callback.answer("Неизвестное действие")
        return

    if status_code == 200:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await callback.answer("Ок")
        await callback.message.answer("Следующая карточка:")
        await send_next_feed_card(callback.message, telegram_id=telegram_id)
        return

    await callback.answer("Ошибка действия", show_alert=True)


async def cmd_upload_photo(message: Message) -> None:
    if not await ensure_profile_exists(message):
        return
    telegram_id = message.from_user.id
    awaiting_photo_upload.add(telegram_id)
    logger.info("/upload_photo: telegram_id=%s", telegram_id)
    await message.answer("Отправь одно фото следующим сообщением.")


async def handle_photo_upload(message: Message) -> None:
    telegram_id = message.from_user.id
    if telegram_id not in awaiting_photo_upload:
        return

    if not message.photo:
        await message.answer("Нужно отправить изображение.")
        return

    buffer = BytesIO()
    await message.bot.download(message.photo[-1], destination=buffer)
    payload = buffer.getvalue()

    status_code, response = await backend.upload_photo(
        telegram_id=telegram_id,
        payload=payload,
        filename=f"tg_{telegram_id}.jpg",
    )
    awaiting_photo_upload.discard(telegram_id)

    if status_code == 200:
        photo = response.get("photo", {})
        logger.info("photo uploaded: telegram_id=%s photo_id=%s", telegram_id, photo.get("id"))
        await message.answer(f"Фото загружено, photo_id={photo.get('id')}")
        return

    logger.warning("photo upload failed: telegram_id=%s status=%s", telegram_id, status_code)
    await message.answer("Не удалось загрузить фото. Проверь формат и размер.")


async def main() -> None:
    if not settings.telegram_bot_token or settings.telegram_bot_token == "change_me":
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN in environment before starting bot service.")

    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()

    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_menu, Command("menu"))
    dp.message.register(cmd_feed, Command("feed"))
    dp.message.register(cmd_matches, Command("matches"))
    dp.message.register(cmd_start_dialog, Command("start_dialog"))
    dp.message.register(cmd_upload_photo, Command("upload_photo"))

    dp.message.register(handle_likes_navigation, F.text.in_(LIKES_NAV_ACTIONS))
    dp.message.register(on_menu_action, F.text.in_(MENU_ACTIONS))

    dp.message.register(create_profile_name, CreateProfileState.name)
    dp.message.register(create_profile_age, CreateProfileState.age)
    dp.message.register(create_profile_gender, CreateProfileState.gender)
    dp.message.register(create_profile_city, CreateProfileState.city)
    dp.message.register(create_profile_bio, CreateProfileState.bio)
    dp.message.register(create_profile_interests, CreateProfileState.interests)
    dp.message.register(create_profile_preferred_gender, CreateProfileState.preferred_gender)
    dp.message.register(create_profile_preferred_age_min, CreateProfileState.preferred_age_min)
    dp.message.register(create_profile_preferred_age_max, CreateProfileState.preferred_age_max)
    dp.message.register(create_profile_finish, CreateProfileState.search_mode)

    dp.message.register(update_profile_pick_field, UpdateProfileState.field)
    dp.message.register(update_profile_set_value, UpdateProfileState.value)

    dp.message.register(handle_photo_upload, F.photo)
    dp.callback_query.register(on_card_action, F.data.startswith("like:"))
    dp.callback_query.register(on_card_action, F.data.startswith("skip:"))
    dp.callback_query.register(on_edit_field, F.data.startswith("edit:"))

    logger.info("Starting Telegram bot")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
