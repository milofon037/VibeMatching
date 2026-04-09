import asyncio
import logging
from collections import defaultdict
from io import BytesIO

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.backend_client import BackendClient
from bot.config import settings
from bot.keyboards import profile_actions_keyboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

backend = BackendClient(base_url=settings.backend_base_url)
last_card_by_user: dict[int, int | None] = defaultdict(lambda: None)
awaiting_photo_upload: set[int] = set()


def _format_profile_card(profile: dict) -> str:
    bio = profile.get("bio") or "-"
    interests = profile.get("interests") or "-"
    return (
        f"ID: {profile['id']}\n"
        f"{profile['name']}, {profile['age']}\n"
        f"Город: {profile['city']}\n"
        f"Пол: {profile['gender']}\n"
        f"Bio: {bio}\n"
        f"Interests: {interests}"
    )


async def send_next_feed_card(message: Message) -> None:
    telegram_id = message.from_user.id
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
    await message.answer(
        _format_profile_card(profile),
        reply_markup=profile_actions_keyboard(int(profile["id"])),
    )


async def cmd_start(message: Message) -> None:
    telegram_id = message.from_user.id
    logger.info("/start: telegram_id=%s", telegram_id)

    status_code, _ = await backend.register_user(telegram_id=telegram_id)
    if status_code not in (200, 201):
        await message.answer("Ошибка регистрации. Попробуйте позже.")
        return

    profile_status, _ = await backend.get_profile_me(telegram_id=telegram_id)
    if profile_status == 404:
        await message.answer(
            "Привет! Давай создадим анкету.\n"
            "Отправь: /create_profile Имя,Возраст,Пол(male|female|other),Город"
        )
        return

    await message.answer("С возвращением! Используй /feed для просмотра ленты.")


async def cmd_create_profile(message: Message) -> None:
    telegram_id = message.from_user.id
    logger.info("/create_profile: telegram_id=%s", telegram_id)
    raw = message.text.removeprefix("/create_profile").strip()
    parts = [part.strip() for part in raw.split(",")]
    if len(parts) != 4:
        await message.answer("Формат: /create_profile Имя,Возраст,Пол,Город")
        return

    name, age_raw, gender, city = parts
    if gender not in {"male", "female", "other"}:
        await message.answer("Пол должен быть male, female или other.")
        return

    try:
        age = int(age_raw)
    except ValueError:
        await message.answer("Возраст должен быть числом.")
        return

    status_code, payload = await backend.create_profile(
        telegram_id=telegram_id,
        payload={"name": name, "age": age, "gender": gender, "city": city},
    )
    if status_code == 200:
        await message.answer(f"Анкета создана: {payload['name']}, {payload['age']}")
        return
    if status_code == 409:
        await message.answer("Анкета уже существует. Используй /update_profile.")
        return
    await message.answer("Не удалось создать анкету.")


async def cmd_update_profile(message: Message) -> None:
    telegram_id = message.from_user.id
    logger.info("/update_profile: telegram_id=%s", telegram_id)
    raw = message.text.removeprefix("/update_profile").strip()
    parts = [part.strip() for part in raw.split(",")]
    if len(parts) != 2:
        await message.answer("Формат: /update_profile Имя,Город")
        return

    name, city = parts
    status_code, payload = await backend.update_profile(
        telegram_id=telegram_id,
        payload={"name": name, "city": city},
    )
    if status_code == 200:
        await message.answer(f"Анкета обновлена: {payload['name']} ({payload['city']})")
        return
    await message.answer("Не удалось обновить анкету.")


async def cmd_feed(message: Message) -> None:
    await send_next_feed_card(message)


async def cmd_matches(message: Message) -> None:
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
        await callback.answer("Ок")
        await callback.message.answer("Следующая карточка:")
        await send_next_feed_card(callback.message)
        return

    await callback.answer("Ошибка действия", show_alert=True)


async def cmd_upload_photo(message: Message) -> None:
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
    dp.message.register(cmd_create_profile, Command("create_profile"))
    dp.message.register(cmd_update_profile, Command("update_profile"))
    dp.message.register(cmd_feed, Command("feed"))
    dp.message.register(cmd_matches, Command("matches"))
    dp.message.register(cmd_start_dialog, Command("start_dialog"))
    dp.message.register(cmd_upload_photo, Command("upload_photo"))
    dp.message.register(handle_photo_upload, F.photo)
    dp.callback_query.register(on_card_action, F.data.startswith("like:"))
    dp.callback_query.register(on_card_action, F.data.startswith("skip:"))

    logger.info("Starting Telegram bot")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
