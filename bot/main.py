import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config import settings
from bot.handlers import register_routers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    if not settings.telegram_bot_token or settings.telegram_bot_token == "change_me":
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN in environment before starting bot service.")

    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()

    register_routers(dp)

    logger.info("Starting Telegram bot")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
