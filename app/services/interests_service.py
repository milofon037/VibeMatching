from starlette import status

from app.core.errors import APIError
from app.repositories.interests_repository import InterestsRepository
from app.repositories.profiles_repository import ProfilesRepository
from app.repositories.users_repository import UsersRepository
from app.services.events_service import LikeEventHandler


class InterestsService:
    def __init__(
        self,
        interests_repository: InterestsRepository,
        profiles_repository: ProfilesRepository,
        users_repository: UsersRepository,
        event_handler: LikeEventHandler,
        session,
    ) -> None:
        self.interests_repository = interests_repository
        self.profiles_repository = profiles_repository
        self.users_repository = users_repository
        self.event_handler = event_handler
        self.session = session

    async def list_interests(self):
        return await self.interests_repository.list_all()

    async def update_my_interests(self, telegram_id: int, interest_ids: list[int]):
        user = await self.users_repository.get_by_telegram_id(telegram_id)
        if user is None:
            raise APIError(
                code="user_not_found",
                message="User is not registered.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        profile = await self.profiles_repository.get_by_user_id(user.id)
        if profile is None:
            raise APIError(
                code="profile_not_found",
                message="Profile is not created yet.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        interests = await self.interests_repository.get_by_ids(interest_ids)
        if len(interests) != len(interest_ids):
            existing_ids = {interest.id for interest in interests}
            unknown_ids = sorted(set(interest_ids) - existing_ids)
            raise APIError(
                code="interests_not_found",
                message=f"Unknown interest ids: {', '.join(str(v) for v in unknown_ids)}",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        updated_profile = await self.profiles_repository.set_interests(profile, interests)
        await self.session.commit()
        await self.event_handler.publish_interests_updated(
            profile_id=updated_profile.id,
            interest_ids=[interest.id for interest in interests],
        )
        return updated_profile
