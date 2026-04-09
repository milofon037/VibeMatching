from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from bot.services.feed_service import feed_service

router = Router(name="feed")

NAV_ACTIONS = {"Следующая", "Выйти"}


@router.message(F.text.in_(NAV_ACTIONS))
async def on_nav_action(message: Message) -> None:
    await feed_service.handle_nav_action(message)


@router.callback_query(F.data == "feed:mode")
async def on_feed_mode(callback: CallbackQuery) -> None:
    await feed_service.handle_feed_mode(callback)


@router.callback_query(F.data.startswith("feed:"))
async def on_feed_action(callback: CallbackQuery) -> None:
    await feed_service.handle_feed_action(callback)


@router.callback_query(F.data.startswith("mode:"))
async def on_mode_change(callback: CallbackQuery) -> None:
    await feed_service.handle_mode_change(callback)


@router.callback_query(F.data.startswith("complaint:"))
async def on_complaint_reason(callback: CallbackQuery) -> None:
    await feed_service.handle_complaint_reason(callback)


@router.callback_query(F.data.startswith("incoming:"))
async def on_incoming_like_action(callback: CallbackQuery) -> None:
    await feed_service.handle_incoming_like_action(callback)
