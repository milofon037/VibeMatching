from __future__ import annotations

from io import BytesIO
from typing import Any

import httpx


class BackendClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def _headers(self, telegram_id: int) -> dict[str, str]:
        return {"X-Telegram-Id": str(telegram_id)}

    async def register_user(self, telegram_id: int) -> tuple[int, dict[str, Any]]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/users/register",
                json={"telegram_id": telegram_id},
            )
            return response.status_code, response.json()

    async def get_profile_me(self, telegram_id: int) -> tuple[int, dict[str, Any]]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self.base_url}/profiles/me",
                headers=self._headers(telegram_id),
            )
            return response.status_code, response.json()

    async def create_profile(self, telegram_id: int, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/profiles/create",
                headers=self._headers(telegram_id),
                json=payload,
            )
            return response.status_code, response.json()

    async def update_profile(self, telegram_id: int, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.patch(
                f"{self.base_url}/profiles/update",
                headers=self._headers(telegram_id),
                json=payload,
            )
            return response.status_code, response.json()

    async def feed(self, telegram_id: int, limit: int = 1) -> tuple[int, list[dict[str, Any]] | dict[str, Any]]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self.base_url}/profiles/feed",
                headers=self._headers(telegram_id),
                params={"limit": limit},
            )
            return response.status_code, response.json()

    async def swipe_like(self, telegram_id: int, to_profile_id: int) -> tuple[int, dict[str, Any]]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/swipe/like",
                headers=self._headers(telegram_id),
                json={"to_profile_id": to_profile_id},
            )
            return response.status_code, response.json()

    async def swipe_skip(self, telegram_id: int, to_profile_id: int) -> tuple[int, dict[str, Any]]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/swipe/skip",
                headers=self._headers(telegram_id),
                json={"to_profile_id": to_profile_id},
            )
            return response.status_code, response.json()

    async def get_matches(self, telegram_id: int) -> tuple[int, list[dict[str, Any]] | dict[str, Any]]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self.base_url}/matches",
                headers=self._headers(telegram_id),
            )
            return response.status_code, response.json()

    async def mark_dialog_started(self, telegram_id: int, match_id: int) -> tuple[int, dict[str, Any]]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/matches/dialog-started",
                headers=self._headers(telegram_id),
                json={"match_id": match_id},
            )
            return response.status_code, response.json()

    async def upload_photo(self, telegram_id: int, payload: bytes, filename: str = "photo.jpg") -> tuple[int, dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/photos/upload",
                headers=self._headers(telegram_id),
                files={"file": (filename, BytesIO(payload), "image/jpeg")},
            )
            return response.status_code, response.json()
