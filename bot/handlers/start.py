from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.services.start_flow import start_flow_service

router = Router(name="start")


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await start_flow_service.handle_start(message)
