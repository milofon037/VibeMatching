from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.errors import APIError
from app.models.enums import SwipeAction
from app.repositories.profiles_repository import ProfilesRepository
from app.repositories.swipes_repository import SwipesRepository
from app.repositories.users_repository import UsersRepository
from app.services.events_service import LikeEventHandler
from app.services.matches_service import MatchesService


class SwipesService:
    def __init__(
        self,
        swipes_repository: SwipesRepository,
        profiles_repository: ProfilesRepository,
        users_repository: UsersRepository,
        like_event_handler: LikeEventHandler,
        matches_service: MatchesService,
        session: AsyncSession,
    ) -> None:
        self.swipes_repository = swipes_repository
        self.profiles_repository = profiles_repository
        self.users_repository = users_repository
        self.like_event_handler = like_event_handler
        self.matches_service = matches_service
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

    async def _create_swipe(self, telegram_id: int, to_profile_id: int, action: SwipeAction):
        user = await self._get_user_by_telegram_id(telegram_id)

        target_profile = await self.profiles_repository.get_by_id(to_profile_id)
        if not target_profile:
            raise APIError(
                code="target_profile_not_found",
                message="Target profile not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if target_profile.user_id == user.id:
            raise APIError(
                code="swipe_self_forbidden",
                message="You cannot swipe your own profile.",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        existing = await self.swipes_repository.get_by_user_and_profile(from_user_id=user.id, to_profile_id=to_profile_id)
        if existing:
            raise APIError(
                code="swipe_already_exists",
                message="You already swiped this profile.",
                status_code=status.HTTP_409_CONFLICT,
            )

        try:
            swipe = await self.swipes_repository.create_swipe(
                from_user_id=user.id,
                to_profile_id=to_profile_id,
                action=action,
            )
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise APIError(
                code="swipe_conflict",
                message="Could not save swipe due to conflicting data.",
                status_code=status.HTTP_409_CONFLICT,
            )

        if action == SwipeAction.LIKE:
            reverse_like = await self.swipes_repository.get_like_to_user_profile(
                from_user_id=target_profile.user_id,
                to_user_id=user.id,
            )
            if reverse_like:
                await self.matches_service.ensure_match(user.id, target_profile.user_id)
                await self.session.commit()
            await self.like_event_handler.publish_like_created(swipe)

        return swipe

    async def like(self, telegram_id: int, to_profile_id: int):
        return await self._create_swipe(telegram_id=telegram_id, to_profile_id=to_profile_id, action=SwipeAction.LIKE)

    async def skip(self, telegram_id: int, to_profile_id: int):
        return await self._create_swipe(telegram_id=telegram_id, to_profile_id=to_profile_id, action=SwipeAction.SKIP)

    async def get_profiles_liked_by_user(self, telegram_id: int, limit: int):
        user = await self._get_user_by_telegram_id(telegram_id)
        return await self.swipes_repository.get_liked_profiles_by_user(from_user_id=user.id, limit=limit)

    async def get_profiles_who_liked_user(self, telegram_id: int, limit: int):
        user = await self._get_user_by_telegram_id(telegram_id)
        return await self.swipes_repository.get_profiles_who_liked_user(to_user_id=user.id, limit=limit)
