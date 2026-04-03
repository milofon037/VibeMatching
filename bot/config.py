import os


class BotSettings:
    def __init__(self) -> None:
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.backend_base_url = os.getenv("BOT_BACKEND_URL", "http://localhost:8000/api/v1")


settings = BotSettings()
