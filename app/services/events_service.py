import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.models.swipe import Swipe

logger = logging.getLogger(__name__)


class LikeEventHandler:
    @staticmethod
    def _build_event(event_type: str, payload: dict[str, Any], dedup_key: str) -> dict[str, Any]:
        return {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "occurred_at": datetime.now(tz=UTC).isoformat(),
            "dedup_key": dedup_key,
            "payload": payload,
        }

    async def publish_like_created(self, swipe: Swipe) -> None:
        event = self._build_event(
            event_type="like_created",
            payload={
                "swipe_id": swipe.id,
                "from_user_id": swipe.from_user_id,
                "to_profile_id": swipe.to_profile_id,
            },
            dedup_key=f"like_created:{swipe.id}",
        )
        # Internal handler for Stage 2: logs event payload until MQ publisher is enabled.
        logger.info("event_published: %s", event)

    async def publish_interests_updated(self, profile_id: int, interest_ids: list[int]) -> None:
        normalized_ids = sorted(set(interest_ids))
        dedup_suffix = ",".join(str(item) for item in normalized_ids)
        event = self._build_event(
            event_type="interests_updated",
            payload={
                "profile_id": profile_id,
                "interest_ids": normalized_ids,
            },
            dedup_key=f"interests_updated:{profile_id}:{dedup_suffix}",
        )
        logger.info("event_published: %s", event)

    async def publish_rating_updated(self, user_id: int, profile_id: int, base_rank: float) -> None:
        event = self._build_event(
            event_type="rating_updated",
            payload={
                "user_id": user_id,
                "profile_id": profile_id,
                "base_rank": base_rank,
            },
            dedup_key=f"rating_updated:{profile_id}:{base_rank:.6f}",
        )
        logger.info("event_published: %s", event)
