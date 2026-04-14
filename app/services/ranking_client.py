from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class RankingServiceUnavailable(Exception):
    pass


@dataclass
class RankedCandidate:
    profile_id: int
    base_rank: float
    interests: list[int]


class RankingServiceClient:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._opened_until: datetime | None = None

    def _is_circuit_open(self) -> bool:
        if self._opened_until is None:
            return False
        return datetime.now(tz=UTC) < self._opened_until

    def _open_circuit(self) -> None:
        self._opened_until = datetime.now(tz=UTC) + timedelta(seconds=30)

    async def rank_feed(
        self,
        user_id: int,
        user_interest_ids: list[int],
        excluded_ids: list[int],
        candidates: list[RankedCandidate],
        limit: int,
    ) -> list[int]:
        if self._is_circuit_open():
            raise RankingServiceUnavailable("circuit_open")

        payload: dict[str, Any] = {
            "user_id": user_id,
            "user_interest_ids": user_interest_ids,
            "excluded_ids": excluded_ids,
            "limit": limit,
            "candidates": [
                {
                    "profile_id": item.profile_id,
                    "base_rank": item.base_rank,
                    "interests": item.interests,
                }
                for item in candidates
            ],
        }

        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(
                        f"{self.base_url}/api/v1/feed/rank",
                        json=payload,
                    )
                response.raise_for_status()
                body = response.json()
                ranked = body.get("ranked_profile_ids", [])
                return [int(item) for item in ranked]
            except (httpx.HTTPError, ValueError, TypeError) as exc:
                logger.warning("ranking service call failed attempt=%s err=%s", attempt + 1, exc)
                if attempt == 1:
                    self._open_circuit()
                    raise RankingServiceUnavailable("request_failed") from exc

        raise RankingServiceUnavailable("request_failed")
