from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SwipeAction
from app.models.profile import Profile
from app.models.swipe import Swipe


class SwipesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user_and_profile(self, from_user_id: int, to_profile_id: int) -> Swipe | None:
        query = select(Swipe).where(
            Swipe.from_user_id == from_user_id,
            Swipe.to_profile_id == to_profile_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_swipe(self, from_user_id: int, to_profile_id: int, action: SwipeAction) -> Swipe:
        swipe = Swipe(from_user_id=from_user_id, to_profile_id=to_profile_id, action=action)
        self.session.add(swipe)
        await self.session.flush()
        await self.session.refresh(swipe)
        return swipe

    async def get_like_to_user_profile(self, from_user_id: int, to_user_id: int) -> Swipe | None:
        query = (
            select(Swipe)
            .join(Profile, Swipe.to_profile_id == Profile.id)
            .where(
                Swipe.from_user_id == from_user_id,
                Swipe.action == SwipeAction.LIKE,
                Profile.user_id == to_user_id,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
