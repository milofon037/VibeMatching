import logging

from app.models.swipe import Swipe

logger = logging.getLogger(__name__)


class LikeEventHandler:
    async def publish_like_created(self, swipe: Swipe) -> None:
        # Internal handler for Stage 2: logs event payload until MQ publisher is enabled.
        logger.info(
            "like_created event: swipe_id=%s from_user_id=%s to_profile_id=%s",
            swipe.id,
            swipe.from_user_id,
            swipe.to_profile_id,
        )
