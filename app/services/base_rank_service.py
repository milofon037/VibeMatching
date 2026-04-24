from datetime import UTC, datetime, timedelta

from app.repositories.matches_repository import MatchesRepository
from app.repositories.photos_repository import PhotosRepository
from app.repositories.profiles_repository import ProfilesRepository
from app.repositories.ratings_repository import RatingsRepository
from app.repositories.swipes_repository import SwipesRepository
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
        swipes_repository: SwipesRepository | None = None,
        matches_repository: MatchesRepository | None = None,
    ) -> None:
        self.users_repository = users_repository
        self.profiles_repository = profiles_repository
        self.photos_repository = photos_repository
        self.ratings_repository = ratings_repository
        self.event_handler = event_handler
        self.swipes_repository = swipes_repository
        self.matches_repository = matches_repository

    async def recalculate_for_user(self, user_id: int) -> float:
        user = await self.users_repository.get_by_id(user_id)
        if user is None:
            return 0.0

        profile = await self.profiles_repository.get_by_user_id(user_id)
        if profile is None:
            return 0.0

        photo_count = await self.photos_repository.count_by_profile_id(profile.id)
        referred_users_count = await self.users_repository.count_referred_users(
            inviter_user_id=user.id,
            inviter_referral_code=user.referral_code,
        )
        likes_received_count = 0
        skips_received_count = 0
        matches_count = 0
        if self.swipes_repository is not None and self.matches_repository is not None:
            week_ago = datetime.now(tz=UTC) - timedelta(days=7)
            likes_received_count, skips_received_count = (
                await self.swipes_repository.get_received_likes_and_skips_count_since(
                    profile_id=profile.id,
                    since=week_ago,
                )
            )
            matches_count = await self.matches_repository.count_recent_for_user(
                user_id=user.id,
                since=week_ago,
            )

        base_rank = calculate_base_rank(
            photo_count=photo_count,
            bio=profile.bio,
            last_active_at=user.last_active_at,
            referred_users_count=referred_users_count,
            likes_received_count=likes_received_count,
            skips_received_count=skips_received_count,
            matches_count=matches_count,
        )
        await self.ratings_repository.upsert_base_rank(user_id=user.id, base_rank=base_rank)
        await self.event_handler.publish_rating_updated(
            user_id=user.id,
            profile_id=profile.id,
            base_rank=base_rank,
        )
        return base_rank
