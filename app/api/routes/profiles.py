from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import resolve_telegram_id
from app.core.database import get_db_session
from app.repositories.profiles_repository import ProfilesRepository
from app.repositories.users_repository import UsersRepository
from app.schemas.profiles import (
    ProfileCreateRequest,
    ProfileResponse,
    ProfileSearchModeRequest,
    ProfileUpdateRequest,
)
from app.services.profiles_service import ProfilesService

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
    )
    profiles = await service.get_feed(telegram_id=telegram_id, limit=limit)
    return [ProfileResponse.model_validate(profile) for profile in profiles]
