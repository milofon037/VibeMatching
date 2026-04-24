from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rating import Rating


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

    async def upsert_base_rank(self, user_id: int, base_rank: float) -> Rating:
        rating = await self.get_by_user_id(user_id)
        if rating is None:
            rating = Rating(user_id=user_id, base_rank=base_rank)
            self.session.add(rating)
            await self.session.flush()
            await self.session.refresh(rating)
            return rating

        rating.base_rank = base_rank
        rating.updated_at = datetime.now(tz=UTC)
        await self.session.flush()
        await self.session.refresh(rating)
        return rating
