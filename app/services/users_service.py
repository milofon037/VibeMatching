from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.errors import APIError
from app.repositories.photos_repository import PhotosRepository
from app.repositories.profiles_repository import ProfilesRepository
from app.repositories.ratings_repository import RatingsRepository
from app.repositories.users_repository import UsersRepository
from app.services.base_rank_service import BaseRankService
from app.services.events_service import LikeEventHandler


class UsersService:
    def __init__(
        self,
        repository: UsersRepository,
        session: AsyncSession,
        profiles_repository: ProfilesRepository | None = None,
        photos_repository: PhotosRepository | None = None,
        ratings_repository: RatingsRepository | None = None,
        event_handler: LikeEventHandler | None = None,
    ) -> None:
        self.repository = repository
        self.session = session
        self.profiles_repository = profiles_repository
        self.photos_repository = photos_repository
        self.ratings_repository = ratings_repository
        self.event_handler = event_handler

    async def _recalculate_base_rank_if_possible(self, user_id: int) -> None:
        if (
            self.profiles_repository is None
            or self.photos_repository is None
            or self.ratings_repository is None
            or self.event_handler is None
        ):
            return

        service = BaseRankService(
            users_repository=self.repository,
            profiles_repository=self.profiles_repository,
            photos_repository=self.photos_repository,
            ratings_repository=self.ratings_repository,
            event_handler=self.event_handler,
        )
        await service.recalculate_for_user(user_id=user_id)

    async def register_user(self, telegram_id: int, referral_code: str | None = None):
        existing = await self.repository.get_by_telegram_id(telegram_id)
        if existing:
            return existing

        try:
            created = await self.repository.create_user(
                telegram_id=telegram_id, referral_code=referral_code
            )
            await self.session.commit()
            return created
        except IntegrityError as err:
            await self.session.rollback()
            fallback = await self.repository.get_by_telegram_id(telegram_id)
            if fallback:
                return fallback
            raise APIError(
                code="user_conflict",
                message="Could not register user because of a conflicting telegram_id.",
                status_code=status.HTTP_409_CONFLICT,
            ) from err

    async def get_current_user(self, telegram_id: int):
        user = await self.repository.get_by_telegram_id(telegram_id)
        if not user:
            raise APIError(
                code="user_not_found",
                message="User is not registered.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return user

    async def update_activity(self, telegram_id: int):
        user = await self.get_current_user(telegram_id)
        updated = await self.repository.update_last_active(user)
        await self._recalculate_base_rank_if_possible(user_id=updated.id)
        await self.session.commit()
        return updated
