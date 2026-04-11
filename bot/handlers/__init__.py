from aiogram import Dispatcher

from bot.handlers.feed import router as feed_router
from bot.handlers.menu import router as menu_router
from bot.handlers.profile import router as profile_router
from bot.handlers.start import router as start_router
from bot.middlewares.activity_and_session import (
    ResetSessionOnMenuMiddleware,
    UserActivityMiddleware,
)


def register_routers(dp: Dispatcher) -> None:
    dp.message.middleware(UserActivityMiddleware())
    dp.callback_query.middleware(UserActivityMiddleware())
    dp.message.middleware(ResetSessionOnMenuMiddleware())

    dp.include_router(start_router)
    dp.include_router(menu_router)
    dp.include_router(profile_router)
    dp.include_router(feed_router)
