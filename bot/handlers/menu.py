from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.services.menu_service import menu_service

router = Router(name="menu")


@router.message(F.text == "Создать анкету")
async def on_create_profile(message: Message, state: FSMContext) -> None:
    await menu_service.on_create_profile(message, state)


@router.message(F.text == "Смотреть анкеты")
async def on_watch_feed(message: Message) -> None:
    await menu_service.on_watch_feed(message)


@router.message(F.text == "Моя анкета")
async def on_my_profile(message: Message) -> None:
    await menu_service.on_my_profile(message)


@router.message(F.text == "Рейтинг")
async def on_rating(message: Message) -> None:
    await menu_service.on_rating(message)


@router.message(F.text == "Изменить режим поиска")
async def on_change_search_mode(message: Message) -> None:
    await menu_service.on_change_search_mode(message)


@router.message(F.text == "Кто меня лайкал")
async def on_incoming_likes(message: Message) -> None:
    await menu_service.on_incoming_likes(message)


@router.message(F.text == "Кого я лайкал")
async def on_outgoing_likes(message: Message) -> None:
    await menu_service.on_outgoing_likes(message)


@router.message(F.text == "Метчи")
async def on_matches(message: Message) -> None:
    await menu_service.on_matches(message)


@router.message(F.text == "Реферальная ссылка")
async def on_referral_link(message: Message) -> None:
    await menu_service.on_referral_link(message)
