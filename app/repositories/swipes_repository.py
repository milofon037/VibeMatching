from datetime import datetime

from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

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

    async def create_swipe(
        self, from_user_id: int, to_profile_id: int, action: SwipeAction
    ) -> Swipe:
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

    async def get_liked_profiles_by_user(self, from_user_id: int, limit: int) -> list[Profile]:
        query = (
            select(Profile)
            .join(Swipe, Swipe.to_profile_id == Profile.id)
            .where(
                Swipe.from_user_id == from_user_id,
                Swipe.action == SwipeAction.LIKE,
            )
            .order_by(desc(Swipe.created_at), desc(Swipe.id))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_profiles_who_liked_user(self, to_user_id: int, limit: int) -> list[Profile]:
        source_profile = aliased(Profile)
        target_profile = aliased(Profile)
        query = (
            select(source_profile)
            .join(Swipe, Swipe.from_user_id == source_profile.user_id)
            .join(target_profile, target_profile.id == Swipe.to_profile_id)
            .where(
                target_profile.user_id == to_user_id,
                Swipe.action == SwipeAction.LIKE,
            )
            .order_by(desc(Swipe.created_at), desc(Swipe.id))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_for_user(self, from_user_id: int, limit: int) -> list[Swipe]:
        query = (
            select(Swipe)
            .where(Swipe.from_user_id == from_user_id)
            .order_by(desc(Swipe.created_at), desc(Swipe.id))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_received_likes_and_skips_count_since(
        self,
        profile_id: int,
        since: datetime,
    ) -> tuple[int, int]:
        query = select(
            func.coalesce(
                func.sum(case((Swipe.action == SwipeAction.LIKE, 1), else_=0)),
                0,
            ),
            func.coalesce(
                func.sum(case((Swipe.action == SwipeAction.SKIP, 1), else_=0)),
                0,
            ),
        ).where(
            Swipe.to_profile_id == profile_id,
            Swipe.created_at >= since,
        )
        result = await self.session.execute(query)
        likes_count, skips_count = result.one()
        return int(likes_count), int(skips_count)
