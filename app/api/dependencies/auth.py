from typing import Annotated

from fastapi import Header, Query
from starlette import status

from app.core.errors import APIError


def resolve_telegram_id(
    x_telegram_id: Annotated[int | None, Header(alias="X-Telegram-Id")] = None,
    telegram_id: Annotated[int | None, Query()] = None,
) -> int:
    value = x_telegram_id if x_telegram_id is not None else telegram_id
    if value is None:
        raise APIError(
            code="telegram_id_required",
            message="Telegram id is required via X-Telegram-Id header or telegram_id query param.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    if value <= 0:
        raise APIError(
            code="telegram_id_invalid",
            message="Telegram id must be a positive integer.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    return value
