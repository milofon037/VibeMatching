from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import SearchCityMode
from app.models.interest import Interest
from app.models.profile import Profile
from app.models.swipe import Swipe


class ProfilesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user_id(self, user_id: int) -> Profile | None:
        query = select(Profile).where(Profile.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, profile_id: int) -> Profile | None:
        query = select(Profile).where(Profile.id == profile_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_ids(self, profile_ids: list[int]) -> list[Profile]:
        if not profile_ids:
            return []

        query = (
            select(Profile)
            .options(selectinload(Profile.interests_catalog))
            .where(Profile.id.in_(profile_ids))
        )
        result = await self.session.execute(query)
        profiles = list(result.scalars().all())
        profile_by_id = {profile.id: profile for profile in profiles}
        return [profile_by_id[profile_id] for profile_id in profile_ids if profile_id in profile_by_id]

    async def create_profile(self, user_id: int, **profile_data) -> Profile:
        profile = Profile(user_id=user_id, **profile_data)
        self.session.add(profile)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def update_profile(self, profile: Profile, **profile_data) -> Profile:
        for field_name, field_value in profile_data.items():
            setattr(profile, field_name, field_value)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def update_search_mode(
        self, profile: Profile, search_city_mode: SearchCityMode
    ) -> Profile:
        profile.search_city_mode = search_city_mode
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def set_interests(self, profile: Profile, interests: list[Interest]) -> Profile:
        profile.interests_catalog = interests
        profile.interests = ", ".join(sorted(interest.name for interest in interests)) if interests else None
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def get_viewed_profile_ids(self, from_user_id: int) -> list[int]:
        query = select(Swipe.to_profile_id).where(Swipe.from_user_id == from_user_id)
        result = await self.session.execute(query)
        return [int(profile_id) for profile_id in result.scalars().all()]

    async def get_feed_profiles(
        self, requester_profile: Profile, from_user_id: int, limit: int
    ) -> list[Profile]:
        viewed_profiles_subquery = select(Swipe.to_profile_id).where(
            Swipe.from_user_id == from_user_id
        )

        query = (
            select(Profile)
            .options(selectinload(Profile.interests_catalog))
            .where(Profile.user_id != from_user_id)
            .where(~Profile.id.in_(viewed_profiles_subquery))
        )

        if requester_profile.preferred_gender is not None:
            query = query.where(Profile.gender == requester_profile.preferred_gender)
        if requester_profile.preferred_age_min is not None:
            query = query.where(Profile.age >= requester_profile.preferred_age_min)
        if requester_profile.preferred_age_max is not None:
            query = query.where(Profile.age <= requester_profile.preferred_age_max)
        if requester_profile.search_city_mode == SearchCityMode.LOCAL:
            query = query.where(Profile.city == requester_profile.city)

        query = query.order_by(Profile.id.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
