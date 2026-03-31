from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.errors import APIError
from app.models.enums import SearchCityMode
from app.repositories.profiles_repository import ProfilesRepository
from app.repositories.users_repository import UsersRepository


class ProfilesService:
    def __init__(
        self,
        profiles_repository: ProfilesRepository,
        users_repository: UsersRepository,
        session: AsyncSession,
    ) -> None:
        self.profiles_repository = profiles_repository
        self.users_repository = users_repository
        self.session = session

    async def _get_user_by_telegram_id(self, telegram_id: int):
        user = await self.users_repository.get_by_telegram_id(telegram_id)
        if not user:
            raise APIError(
                code="user_not_found",
                message="User is not registered.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return user

    async def create_profile(self, telegram_id: int, profile_data: dict):
        user = await self._get_user_by_telegram_id(telegram_id)

        existing = await self.profiles_repository.get_by_user_id(user.id)
        if existing:
            raise APIError(
                code="profile_already_exists",
                message="User already has an active profile.",
                status_code=status.HTTP_409_CONFLICT,
            )

        try:
            profile = await self.profiles_repository.create_profile(user_id=user.id, **profile_data)
            await self.session.commit()
            return profile
        except IntegrityError:
            await self.session.rollback()
            raise APIError(
                code="profile_conflict",
                message="Could not create profile because of conflicting data.",
                status_code=status.HTTP_409_CONFLICT,
            )

    async def get_my_profile(self, telegram_id: int):
        user = await self._get_user_by_telegram_id(telegram_id)
        profile = await self.profiles_repository.get_by_user_id(user.id)
        if not profile:
            raise APIError(
                code="profile_not_found",
                message="Profile is not created yet.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return profile

    async def update_profile(self, telegram_id: int, profile_data: dict):
        profile = await self.get_my_profile(telegram_id)
        try:
            updated = await self.profiles_repository.update_profile(profile, **profile_data)
            await self.session.commit()
            return updated
        except IntegrityError:
            await self.session.rollback()
            raise APIError(
                code="profile_update_conflict",
                message="Could not update profile because of conflicting data.",
                status_code=status.HTTP_409_CONFLICT,
            )

    async def update_search_mode(self, telegram_id: int, search_city_mode: SearchCityMode):
        profile = await self.get_my_profile(telegram_id)
        updated = await self.profiles_repository.update_search_mode(profile, search_city_mode=search_city_mode)
        await self.session.commit()
        return updated
