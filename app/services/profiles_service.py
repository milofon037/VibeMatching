from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.config import settings
from app.core.errors import APIError
from app.models.enums import SearchCityMode
from app.repositories.photos_repository import PhotosRepository
from app.repositories.profiles_repository import ProfilesRepository
from app.repositories.ratings_repository import RatingsRepository
from app.repositories.matches_repository import MatchesRepository
from app.repositories.swipes_repository import SwipesRepository
from app.repositories.users_repository import UsersRepository
from app.services.base_rank_service import BaseRankService
from app.services.events_service import LikeEventHandler
from app.services.feed_cache_service import FeedCacheService
from app.services.ranking_client import (
    RankedCandidate,
    RankingServiceClient,
    RankingServiceUnavailable,
)


class ProfilesService:
    def __init__(
        self,
        profiles_repository: ProfilesRepository,
        users_repository: UsersRepository,
        session: AsyncSession,
        ratings_repository: RatingsRepository | None = None,
        ranking_client: RankingServiceClient | None = None,
        photos_repository: PhotosRepository | None = None,
        event_handler: LikeEventHandler | None = None,
        feed_cache_service: FeedCacheService | None = None,
        swipes_repository: SwipesRepository | None = None,
        matches_repository: MatchesRepository | None = None,
    ) -> None:
        self.profiles_repository = profiles_repository
        self.users_repository = users_repository
        self.session = session
        self.ratings_repository = ratings_repository
        self.ranking_client = ranking_client
        self.photos_repository = photos_repository
        self.event_handler = event_handler
        self.feed_cache_service = feed_cache_service
        self.swipes_repository = swipes_repository
        self.matches_repository = matches_repository

    async def _rank_candidates(
        self,
        *,
        user_id: int,
        my_interest_ids: list[int],
        candidates: list,
        limit: int,
    ):
        if not settings.ranking_service_enabled or self.ranking_client is None:
            return candidates
        if self.ratings_repository is None:
            return candidates

        viewed_ids = await self.profiles_repository.get_viewed_profile_ids(from_user_id=user_id)
        base_rank_by_user_id = await self.ratings_repository.get_base_ranks_by_user_ids(
            [profile.user_id for profile in candidates]
        )
        candidate_payload = [
            RankedCandidate(
                profile_id=profile.id,
                base_rank=base_rank_by_user_id.get(profile.user_id, 0.0),
                interests=[interest.id for interest in profile.interests_catalog],
            )
            for profile in candidates
        ]

        try:
            ranked_profile_ids = await self.ranking_client.rank_feed(
                user_id=user_id,
                user_interest_ids=my_interest_ids,
                excluded_ids=viewed_ids,
                candidates=candidate_payload,
                limit=limit,
            )
        except RankingServiceUnavailable:
            return candidates

        profile_by_id = {profile.id: profile for profile in candidates}
        ranked_profiles = [
            profile_by_id[profile_id] for profile_id in ranked_profile_ids if profile_id in profile_by_id
        ]
        if ranked_profiles:
            return ranked_profiles
        return candidates

    async def _recalculate_base_rank_if_possible(self, user_id: int) -> bool:
        if (
            self.ratings_repository is None
            or self.photos_repository is None
            or self.event_handler is None
        ):
            return False

        service = BaseRankService(
            users_repository=self.users_repository,
            profiles_repository=self.profiles_repository,
            photos_repository=self.photos_repository,
            ratings_repository=self.ratings_repository,
            event_handler=self.event_handler,
            swipes_repository=self.swipes_repository,
            matches_repository=self.matches_repository,
        )
        await service.recalculate_for_user(user_id=user_id)
        return True

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
            await self._recalculate_base_rank_if_possible(user_id=user.id)
            await self.session.commit()
            return profile
        except IntegrityError as err:
            await self.session.rollback()
            raise APIError(
                code="profile_conflict",
                message="Could not create profile because of conflicting data.",
                status_code=status.HTTP_409_CONFLICT,
            ) from err

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
            await self._recalculate_base_rank_if_possible(user_id=updated.user_id)
            await self.session.commit()
            return updated
        except IntegrityError as err:
            await self.session.rollback()
            raise APIError(
                code="profile_update_conflict",
                message="Could not update profile because of conflicting data.",
                status_code=status.HTTP_409_CONFLICT,
            ) from err

    async def update_search_mode(self, telegram_id: int, search_city_mode: SearchCityMode):
        profile = await self.get_my_profile(telegram_id)
        updated = await self.profiles_repository.update_search_mode(
            profile, search_city_mode=search_city_mode
        )
        await self.session.commit()
        return updated

    async def get_feed(self, telegram_id: int, limit: int | None = None):
        user = await self._get_user_by_telegram_id(telegram_id)
        my_profile = await self.profiles_repository.get_by_user_id(user.id)
        if not my_profile:
            raise APIError(
                code="profile_not_found",
                message="Profile is not created yet.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        batch_limit = settings.feed_batch_size if limit is None else limit
        if batch_limit <= 0:
            raise APIError(
                code="feed_limit_invalid",
                message="Feed limit must be a positive integer.",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        if batch_limit > settings.feed_batch_size:
            batch_limit = settings.feed_batch_size

        # Keep personal rating up-to-date before feed ranking.
        recalculated = await self._recalculate_base_rank_if_possible(user_id=user.id)
        if recalculated:
            await self.session.commit()

        if settings.feed_cache_enabled and self.feed_cache_service is not None:
            cached_ids = await self.feed_cache_service.get_cached_profile_ids(
                user_id=user.id,
                limit=batch_limit,
            )
            if len(cached_ids) == batch_limit:
                cached_profiles = await self.profiles_repository.get_by_ids(cached_ids)
                if len(cached_profiles) == batch_limit:
                    await self.feed_cache_service.consume(user_id=user.id, count=batch_limit)
                    return cached_profiles

        feed_window_size = batch_limit
        if settings.feed_cache_enabled and self.feed_cache_service is not None:
            feed_window_size += max(0, settings.feed_cache_batch_size)

        candidates = await self.profiles_repository.get_feed_profiles(
            requester_profile=my_profile,
            from_user_id=user.id,
            limit=feed_window_size,
        )
        ranked_profiles = await self._rank_candidates(
            user_id=user.id,
            my_interest_ids=[interest.id for interest in my_profile.interests_catalog],
            candidates=candidates,
            limit=feed_window_size,
        )

        response_profiles = ranked_profiles[:batch_limit]
        if settings.feed_cache_enabled and self.feed_cache_service is not None:
            cached_profiles = ranked_profiles[batch_limit : batch_limit + settings.feed_cache_batch_size]
            await self.feed_cache_service.replace_cache(
                user_id=user.id,
                profile_ids=[profile.id for profile in cached_profiles],
            )

        return response_profiles
