from datetime import UTC, datetime
from math import isclose

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rating import Rating
from app.models.rating_history import RatingHistory


_HISTORY_DELTA_SCALE = 1000


class RatingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user_id(self, user_id: int) -> Rating | None:
        query = select(Rating).where(Rating.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_base_ranks_by_user_ids(self, user_ids: list[int]) -> dict[int, float]:
        if not user_ids:
            return {}
        query = select(Rating.user_id, Rating.base_rank).where(Rating.user_id.in_(user_ids))
        result = await self.session.execute(query)
        rows = result.all()
        return {int(user_id): float(base_rank) for user_id, base_rank in rows}

    async def _create_history_record(
        self,
        *,
        user_id: int,
        event_type: str,
        previous_base_rank: float,
        next_base_rank: float,
    ) -> None:
        if isclose(previous_base_rank, next_base_rank, rel_tol=0.0, abs_tol=1e-12):
            return

        delta = int(round((next_base_rank - previous_base_rank) * _HISTORY_DELTA_SCALE))
        if delta == 0:
            delta = 1 if next_base_rank > previous_base_rank else -1

        self.session.add(
            RatingHistory(
                user_id=user_id,
                event_type=event_type,
                delta=delta,
            )
        )

    async def upsert_base_rank(self, user_id: int, base_rank: float) -> Rating:
        rating = await self.get_by_user_id(user_id)
        if rating is None:
            rating = Rating(user_id=user_id, base_rank=base_rank)
            self.session.add(rating)
            await self._create_history_record(
                user_id=user_id,
                event_type="base_rank_initialized",
                previous_base_rank=0.0,
                next_base_rank=base_rank,
            )
            await self.session.flush()
            await self.session.refresh(rating)
            return rating

        previous_base_rank = float(rating.base_rank)
        rating.base_rank = base_rank
        rating.updated_at = datetime.now(tz=UTC)
        await self._create_history_record(
            user_id=user_id,
            event_type="base_rank_recalculated",
            previous_base_rank=previous_base_rank,
            next_base_rank=base_rank,
        )
        await self.session.flush()
        await self.session.refresh(rating)
        return rating
