from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.match import Match


class MatchesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_pair(self, user1_id: int, user2_id: int) -> Match | None:
        first, second = sorted((user1_id, user2_id))
        query = select(Match).where(Match.user1_id == first, Match.user2_id == second)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_match(self, user1_id: int, user2_id: int) -> Match:
        first, second = sorted((user1_id, user2_id))
        match = Match(user1_id=first, user2_id=second)
        self.session.add(match)
        await self.session.flush()
        await self.session.refresh(match)
        return match

    async def list_for_user(self, user_id: int) -> list[Match]:
        query = (
            select(Match)
            .where(or_(Match.user1_id == user_id, Match.user2_id == user_id))
            .order_by(Match.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_for_user_by_id(self, user_id: int, match_id: int) -> Match | None:
        query = select(Match).where(
            Match.id == match_id,
            or_(Match.user1_id == user_id, Match.user2_id == user_id),
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def mark_dialog_started(self, match: Match) -> Match:
        match.dialog_started = True
        await self.session.flush()
        await self.session.refresh(match)
        return match
