from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SearchCityMode
from app.models.profile import Profile


class ProfilesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_user_id(self, user_id: int) -> Profile | None:
        query = select(Profile).where(Profile.user_id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

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

    async def update_search_mode(self, profile: Profile, search_city_mode: SearchCityMode) -> Profile:
        profile.search_city_mode = search_city_mode
        await self.session.flush()
        await self.session.refresh(profile)
        return profile
