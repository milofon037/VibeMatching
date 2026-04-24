from __future__ import annotations

from io import BytesIO
from typing import Any

import httpx


class BackendClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def _headers(self, telegram_id: int) -> dict[str, str]:
        return {"X-Telegram-Id": str(telegram_id)}

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        telegram_id: int | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        timeout: float = 15.0,
    ) -> tuple[int, Any]:
        headers = self._headers(telegram_id) if telegram_id is not None else None
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                request_fn = getattr(client, method.lower())
                request_kwargs: dict[str, Any] = {"url": f"{self.base_url}{path}"}
                if headers is not None:
                    request_kwargs["headers"] = headers
                if params is not None:
                    request_kwargs["params"] = params
                if json is not None:
                    request_kwargs["json"] = json
                if files is not None:
                    request_kwargs["files"] = files

                response = await request_fn(**request_kwargs)
            return response.status_code, response.json()
        except (httpx.HTTPError, ValueError):
            return 503, {"code": "backend_unavailable", "message": "Backend is unavailable"}

    async def _request_bytes(
        self,
        method: str,
        path: str,
        *,
        timeout: float = 20.0,
    ) -> tuple[int, bytes, str | None]:
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                request_fn = getattr(client, method.lower())
                response = await request_fn(url=f"{self.base_url}{path}")
            return response.status_code, response.content, response.headers.get("content-type")
        except httpx.HTTPError:
            return 503, b"", None

    async def register_user(self, telegram_id: int) -> tuple[int, dict[str, Any]]:
        status_code, payload = await self._request_json(
            "POST", "/users/register", json={"telegram_id": telegram_id}
        )
        return status_code, dict(payload)

    async def update_activity(self, telegram_id: int) -> tuple[int, dict[str, Any]]:
        status_code, payload = await self._request_json(
            "PATCH", "/users/activity", telegram_id=telegram_id
        )
        return status_code, dict(payload)

    async def get_profile_me(self, telegram_id: int) -> tuple[int, dict[str, Any]]:
        status_code, payload = await self._request_json(
            "GET", "/profiles/me", telegram_id=telegram_id
        )
        return status_code, dict(payload)

    async def create_profile(
        self, telegram_id: int, payload: dict[str, Any]
    ) -> tuple[int, dict[str, Any]]:
        status_code, response_payload = await self._request_json(
            "POST", "/profiles/create", telegram_id=telegram_id, json=payload
        )
        return status_code, dict(response_payload)

    async def update_profile(
        self, telegram_id: int, payload: dict[str, Any]
    ) -> tuple[int, dict[str, Any]]:
        status_code, response_payload = await self._request_json(
            "PATCH", "/profiles/update", telegram_id=telegram_id, json=payload
        )
        return status_code, dict(response_payload)

    async def update_search_mode(
        self, telegram_id: int, search_city_mode: str
    ) -> tuple[int, dict[str, Any]]:
        status_code, payload = await self._request_json(
            "PATCH",
            "/profiles/search-mode",
            telegram_id=telegram_id,
            json={"search_city_mode": search_city_mode},
        )
        return status_code, dict(payload)

    async def feed(
        self, telegram_id: int, limit: int = 1
    ) -> tuple[int, list[dict[str, Any]] | dict[str, Any]]:
        return await self._request_json(
            "GET", "/profiles/feed", telegram_id=telegram_id, params={"limit": limit}
        )

    async def list_interests(self) -> tuple[int, list[dict[str, Any]] | dict[str, Any]]:
        return await self._request_json("GET", "/interests")

    async def update_profile_interests(
        self, telegram_id: int, interest_ids: list[int]
    ) -> tuple[int, dict[str, Any]]:
        status_code, payload = await self._request_json(
            "PATCH",
            "/profiles/interests",
            telegram_id=telegram_id,
            json={"interest_ids": interest_ids},
        )
        return status_code, dict(payload)

    async def swipe_like(self, telegram_id: int, to_profile_id: int) -> tuple[int, dict[str, Any]]:
        status_code, payload = await self._request_json(
            "POST", f"/swipes/like/{to_profile_id}", telegram_id=telegram_id
        )
        return status_code, dict(payload)

    async def swipe_skip(self, telegram_id: int, to_profile_id: int) -> tuple[int, dict[str, Any]]:
        status_code, payload = await self._request_json(
            "POST", f"/swipes/skip/{to_profile_id}", telegram_id=telegram_id
        )
        return status_code, dict(payload)

    async def get_matches(
        self, telegram_id: int
    ) -> tuple[int, list[dict[str, Any]] | dict[str, Any]]:
        return await self._request_json("GET", "/matches/list", telegram_id=telegram_id)

    async def upload_photo(
        self, telegram_id: int, payload: bytes, filename: str = "photo.jpg"
    ) -> tuple[int, dict[str, Any]]:
        status_code, response_payload = await self._request_json(
            "POST",
            "/photos/upload",
            telegram_id=telegram_id,
            files={"file": (filename, BytesIO(payload), "image/jpeg")},
            timeout=30.0,
        )
        return status_code, dict(response_payload)

    async def outgoing_likes(
        self, telegram_id: int, limit: int = 20
    ) -> tuple[int, list[dict[str, Any]] | dict[str, Any]]:
        return await self._request_json(
            "GET", "/swipes/likes/outgoing", telegram_id=telegram_id, params={"limit": limit}
        )

    async def incoming_likes(
        self, telegram_id: int, limit: int = 20
    ) -> tuple[int, list[dict[str, Any]] | dict[str, Any]]:
        return await self._request_json(
            "GET", "/swipes/likes/incoming", telegram_id=telegram_id, params={"limit": limit}
        )

    async def get_profile_photos(
        self, profile_id: int
    ) -> tuple[int, list[dict[str, Any]] | dict[str, Any]]:
        return await self._request_json("GET", f"/photos/profile/{profile_id}")

    async def get_primary_profile_photo_raw(self, profile_id: int) -> tuple[int, bytes, str | None]:
        return await self._request_bytes("GET", f"/photos/profile/{profile_id}/primary/raw")
