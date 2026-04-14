from app.repositories.photos_repository import PhotosRepository
from app.repositories.profiles_repository import ProfilesRepository
from app.repositories.ratings_repository import RatingsRepository
from app.repositories.users_repository import UsersRepository
from app.services.events_service import LikeEventHandler
from app.services.rating_score import calculate_base_rank


class BaseRankService:
    def __init__(
        self,
        users_repository: UsersRepository,
        profiles_repository: ProfilesRepository,
        photos_repository: PhotosRepository,
        ratings_repository: RatingsRepository,
        event_handler: LikeEventHandler,
    ) -> None:
        self.users_repository = users_repository
        self.profiles_repository = profiles_repository
        self.photos_repository = photos_repository
        self.ratings_repository = ratings_repository
        self.event_handler = event_handler

    async def recalculate_for_user(self, user_id: int) -> float:
        user = await self.users_repository.get_by_id(user_id)
        if user is None:
            return 0.0

        profile = await self.profiles_repository.get_by_user_id(user_id)
        if profile is None:
            return 0.0

        photo_count = await self.photos_repository.count_by_profile_id(profile.id)
        base_rank = calculate_base_rank(
            photo_count=photo_count,
            bio=profile.bio,
            last_active_at=user.last_active_at,
        )
        await self.ratings_repository.upsert_base_rank(user_id=user.id, base_rank=base_rank)
        await self.event_handler.publish_rating_updated(
            user_id=user.id,
            profile_id=profile.id,
            base_rank=base_rank,
        )
        return base_rank
