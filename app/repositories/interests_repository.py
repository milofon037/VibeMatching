from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interest import Interest


class InterestsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self) -> list[Interest]:
        query = select(Interest).order_by(Interest.name.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_ids(self, interest_ids: list[int]) -> list[Interest]:
        if not interest_ids:
            return []
        query = select(Interest).where(Interest.id.in_(interest_ids))
        result = await self.session.execute(query)
        return list(result.scalars().all())
