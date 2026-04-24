from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

import httpx

logger = logging.getLogger(__name__)


class ProfilesIndexRepository(Protocol):
    async def ensure_index(self) -> None:
        ...

    async def upsert(
        self,
        profile_id: int,
        *,
        interests: list[int] | None = None,
        base_rank: float | None = None,
    ) -> None:
        ...


@dataclass
class InMemoryProfilesIndexRepository:
    documents: dict[int, dict[str, Any]] = field(default_factory=dict)

    async def ensure_index(self) -> None:
        return None

    async def upsert(
        self,
        profile_id: int,
        *,
        interests: list[int] | None = None,
        base_rank: float | None = None,
    ) -> None:
        current = self.documents.get(profile_id, {"profile_id": profile_id})
        if interests is not None:
            current["interests"] = interests
        if base_rank is not None:
            current["base_rank"] = base_rank
        self.documents[profile_id] = current


class ElasticsearchProfilesIndexRepository:
    def __init__(self, base_url: str, index_name: str, timeout_seconds: float = 3.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.index_name = index_name
        self.timeout_seconds = timeout_seconds

    async def ensure_index(self) -> None:
        index_url = f"{self.base_url}/{self.index_name}"
        mapping = {
            "mappings": {
                "properties": {
                    "profile_id": {"type": "integer"},
                    "interests": {"type": "integer"},
                    "base_rank": {"type": "float"},
                    "is_global": {"type": "boolean"},
                    "last_active": {"type": "date"},
                }
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            head_response = await client.head(index_url)
            if head_response.status_code == 200:
                return
            if head_response.status_code not in (404,):
                head_response.raise_for_status()

            put_response = await client.put(index_url, json=mapping)
            if put_response.status_code in (200, 201):
                logger.info("created_profiles_index index=%s", self.index_name)
                return
            put_response.raise_for_status()

    async def upsert(
        self,
        profile_id: int,
        *,
        interests: list[int] | None = None,
        base_rank: float | None = None,
    ) -> None:
        update_doc: dict[str, Any] = {"profile_id": profile_id}
        if interests is not None:
            update_doc["interests"] = interests
        if base_rank is not None:
            update_doc["base_rank"] = float(base_rank)
        update_doc["updated_at"] = datetime.now(tz=UTC).isoformat()

        body = {
            "doc": update_doc,
            "doc_as_upsert": True,
            "upsert": {
                "profile_id": profile_id,
                "interests": [],
                "base_rank": 0.0,
                "is_global": False,
                "last_active": None,
                **update_doc,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/{self.index_name}/_update/{profile_id}",
                json=body,
            )
            response.raise_for_status()
