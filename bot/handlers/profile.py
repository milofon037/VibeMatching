from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.services.profile_service import profile_service
from bot.states.profile import CreateProfileState, UpdateProfileState

router = Router(name="profile")


@router.message(CreateProfileState.name)
async def create_profile_name(message: Message, state: FSMContext) -> None:
    await profile_service.handle_create_profile_name(message, state)


@router.message(CreateProfileState.age)
async def create_profile_age(message: Message, state: FSMContext) -> None:
    await profile_service.handle_create_profile_age(message, state)


@router.message(CreateProfileState.city)
async def create_profile_city(message: Message, state: FSMContext) -> None:
    await profile_service.handle_create_profile_city(message, state)


@router.message(CreateProfileState.bio, F.text)
async def create_profile_bio(message: Message, state: FSMContext) -> None:
    await profile_service.handle_create_profile_bio(message, state)


@router.message(CreateProfileState.interests, F.text)
async def create_profile_interests(message: Message, state: FSMContext) -> None:
    await profile_service.handle_create_profile_interests(message, state)


@router.message(UpdateProfileState.value)
async def update_profile_value(message: Message, state: FSMContext) -> None:
    await profile_service.handle_update_profile_value(message, state)


@router.message(CreateProfileState.photo, F.photo)
async def handle_create_profile_photo(message: Message, state: FSMContext) -> None:
    await profile_service.handle_photo_upload(message, state)


@router.message(CreateProfileState.photo)
async def handle_create_profile_photo_invalid(message: Message) -> None:
    await profile_service.handle_waiting_profile_photo_invalid(message)


@router.message(F.photo)
async def handle_photo_upload(message: Message, state: FSMContext) -> None:
    await profile_service.handle_photo_upload(message, state)


@router.callback_query(F.data.startswith("answer:"))
async def on_answer_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await profile_service.handle_answer_callback(callback, state)


@router.callback_query(F.data.startswith("edit:"))
async def on_edit_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await profile_service.handle_edit_callback(callback, state)
