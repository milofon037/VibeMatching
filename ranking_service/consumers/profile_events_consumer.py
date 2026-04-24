from __future__ import annotations

from typing import Any

from ranking_service.repositories.profiles_index import ProfilesIndexRepository


class ProfileEventsConsumer:
    def __init__(self, index_repository: ProfilesIndexRepository) -> None:
        self.index_repository = index_repository
        self._seen_event_ids: set[str] = set()
        self._seen_dedup_keys: set[str] = set()
        self._is_initialized = False

    async def initialize(self) -> None:
        if self._is_initialized:
            return
        await self.index_repository.ensure_index()
        self._is_initialized = True

    async def process(self, event: dict[str, Any]) -> bool:
        await self.initialize()

        event_id = str(event.get("event_id", ""))
        dedup_key = str(event.get("dedup_key", ""))
        if not event_id or not dedup_key:
            return False

        if event_id in self._seen_event_ids or dedup_key in self._seen_dedup_keys:
            return False

        payload = event.get("payload", {})
        event_type = event.get("event_type")

        if event_type == "interests_updated":
            profile_id = int(payload["profile_id"])
            interest_ids = [int(item) for item in payload.get("interest_ids", [])]
            await self.index_repository.upsert(profile_id=profile_id, interests=interest_ids)
        elif event_type == "rating_updated":
            profile_id = int(payload["profile_id"])
            base_rank = float(payload["base_rank"])
            await self.index_repository.upsert(profile_id=profile_id, base_rank=base_rank)
        else:
            return False

        self._seen_event_ids.add(event_id)
        self._seen_dedup_keys.add(dedup_key)
        return True
