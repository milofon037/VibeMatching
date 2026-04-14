from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import resolve_telegram_id
from app.core.config import settings
from app.core.database import get_db_session
from app.repositories.interests_repository import InterestsRepository
from app.repositories.photos_repository import PhotosRepository
from app.repositories.profiles_repository import ProfilesRepository
from app.repositories.ratings_repository import RatingsRepository
from app.repositories.users_repository import UsersRepository
from app.schemas.interests import ProfileInterestsUpdateRequest
from app.schemas.profiles import (
    ProfileCreateRequest,
    ProfileResponse,
    ProfileSearchModeRequest,
    ProfileUpdateRequest,
)
from app.services.events_service import LikeEventHandler
from app.services.interests_service import InterestsService
from app.services.profiles_service import ProfilesService
from app.services.ranking_client import RankingServiceClient

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("/create", response_model=ProfileResponse)
async def create_profile(
    payload: ProfileCreateRequest,
    telegram_id: Annotated[int, Depends(resolve_telegram_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProfileResponse:
    service = ProfilesService(
        profiles_repository=ProfilesRepository(session=session),
        users_repository=UsersRepository(session=session),
        session=session,
        ratings_repository=RatingsRepository(session=session),
        ranking_client=RankingServiceClient(
            base_url=settings.ranking_service_url,
            timeout_seconds=settings.ranking_service_timeout_seconds,
        ),
        photos_repository=PhotosRepository(session=session),
        event_handler=LikeEventHandler(),
    )
    profile = await service.create_profile(
        telegram_id=telegram_id, profile_data=payload.model_dump()
    )
    return ProfileResponse.model_validate(profile)


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    telegram_id: Annotated[int, Depends(resolve_telegram_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProfileResponse:
    service = ProfilesService(
        profiles_repository=ProfilesRepository(session=session),
        users_repository=UsersRepository(session=session),
        session=session,
        ratings_repository=RatingsRepository(session=session),
        ranking_client=RankingServiceClient(
            base_url=settings.ranking_service_url,
            timeout_seconds=settings.ranking_service_timeout_seconds,
        ),
        photos_repository=PhotosRepository(session=session),
        event_handler=LikeEventHandler(),
    )
    profile = await service.get_my_profile(telegram_id=telegram_id)
    return ProfileResponse.model_validate(profile)


@router.patch("/update", response_model=ProfileResponse)
async def update_profile(
    payload: ProfileUpdateRequest,
    telegram_id: Annotated[int, Depends(resolve_telegram_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProfileResponse:
    service = ProfilesService(
        profiles_repository=ProfilesRepository(session=session),
        users_repository=UsersRepository(session=session),
        session=session,
        ratings_repository=RatingsRepository(session=session),
        ranking_client=RankingServiceClient(
            base_url=settings.ranking_service_url,
            timeout_seconds=settings.ranking_service_timeout_seconds,
        ),
        photos_repository=PhotosRepository(session=session),
        event_handler=LikeEventHandler(),
    )
    profile = await service.update_profile(
        telegram_id=telegram_id,
        profile_data=payload.model_dump(exclude_none=True),
    )
    return ProfileResponse.model_validate(profile)


@router.patch("/search-mode", response_model=ProfileResponse)
async def update_search_mode(
    payload: ProfileSearchModeRequest,
    telegram_id: Annotated[int, Depends(resolve_telegram_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProfileResponse:
    service = ProfilesService(
        profiles_repository=ProfilesRepository(session=session),
        users_repository=UsersRepository(session=session),
        session=session,
        ratings_repository=RatingsRepository(session=session),
        ranking_client=RankingServiceClient(
            base_url=settings.ranking_service_url,
            timeout_seconds=settings.ranking_service_timeout_seconds,
        ),
        photos_repository=PhotosRepository(session=session),
        event_handler=LikeEventHandler(),
    )
    profile = await service.update_search_mode(
        telegram_id=telegram_id,
        search_city_mode=payload.search_city_mode,
    )
    return ProfileResponse.model_validate(profile)


@router.get("/feed", response_model=list[ProfileResponse])
async def get_feed(
    telegram_id: Annotated[int, Depends(resolve_telegram_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int | None = Query(default=None, ge=1),
) -> list[ProfileResponse]:
    service = ProfilesService(
        profiles_repository=ProfilesRepository(session=session),
        users_repository=UsersRepository(session=session),
        session=session,
        ratings_repository=RatingsRepository(session=session),
        ranking_client=RankingServiceClient(
            base_url=settings.ranking_service_url,
            timeout_seconds=settings.ranking_service_timeout_seconds,
        ),
        photos_repository=PhotosRepository(session=session),
        event_handler=LikeEventHandler(),
    )
    profiles = await service.get_feed(telegram_id=telegram_id, limit=limit)
    return [ProfileResponse.model_validate(profile) for profile in profiles]


@router.patch("/interests", response_model=ProfileResponse)
async def update_profile_interests(
    payload: ProfileInterestsUpdateRequest,
    telegram_id: Annotated[int, Depends(resolve_telegram_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProfileResponse:
    service = InterestsService(
        interests_repository=InterestsRepository(session=session),
        profiles_repository=ProfilesRepository(session=session),
        users_repository=UsersRepository(session=session),
        event_handler=LikeEventHandler(),
        session=session,
    )
    profile = await service.update_my_interests(
        telegram_id=telegram_id,
        interest_ids=payload.interest_ids,
    )
    return ProfileResponse.model_validate(profile)
