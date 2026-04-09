from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

from aiogram.types import Message
from aiogram.types.input_file import BufferedInputFile

from bot.utils.context import api_client
from bot.utils.formatters import format_profile_card

logger = logging.getLogger(__name__)


async def get_primary_photo_url(profile_id: int) -> str | None:
    status_code, payload = await api_client.get_profile_photos(profile_id=profile_id)
    if status_code != 200 or not isinstance(payload, list) or not payload:
        return None

    sorted_photos = sorted(payload, key=lambda photo: photo.get("position", 10_000))
    photo_url = sorted_photos[0].get("photo_url")
    return photo_url if isinstance(photo_url, str) and photo_url else None


async def send_profile_card(
    message: Message,
    profile: dict[str, Any],
    title: str | None = None,
    reply_markup=None,
) -> None:
    caption = format_profile_card(profile)
    if title:
        caption = f"{title}\n\n{caption}"

    photo_url = await get_primary_photo_url(profile_id=int(profile["id"]))
    if photo_url:
        parsed_url = urlparse(photo_url)

        if parsed_url.scheme in {"http", "https"}:
            try:
                await message.answer_photo(photo=photo_url, caption=caption, reply_markup=reply_markup)
                return
            except Exception as exc:
                logger.warning("failed to send photo by url for profile_id=%s: %s", profile.get("id"), exc)

        # For private object storage (s3://...) and failed public URLs, ask backend
        # for raw bytes of the primary photo and upload it directly to Telegram.
        status_code, payload, content_type = await api_client.get_primary_profile_photo_raw(int(profile["id"]))
        if status_code == 200 and payload:
            file_ext = ".jpg"
            if content_type == "image/png":
                file_ext = ".png"
            elif content_type == "image/webp":
                file_ext = ".webp"

            await message.answer_photo(
                photo=BufferedInputFile(payload, filename=f"profile{file_ext}"),
                caption=caption,
                reply_markup=reply_markup,
            )
            return

        logger.warning(
            "failed to send photo by backend raw endpoint for profile_id=%s status=%s",
            profile.get("id"),
            status_code,
        )

    await message.answer(caption, reply_markup=reply_markup)
