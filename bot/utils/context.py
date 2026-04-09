from __future__ import annotations

from typing import Any

from bot.config import settings
from bot.services.api_client import BackendClient

api_client = BackendClient(base_url=settings.backend_base_url)

# In-memory per-user session state for interactive list flows.
user_sessions: dict[int, dict[str, Any]] = {}

# In-memory per-user flag to await profile photo upload.
awaiting_photo_upload: dict[int, dict[str, Any]] = {}
