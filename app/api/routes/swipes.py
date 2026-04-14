from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import resolve_telegram_id
from app.core.database import get_db_session
from app.repositories.matches_repository import MatchesRepository
from app.repositories.profiles_repository import ProfilesRepository
from app.repositories.swipes_repository import SwipesRepository
from app.repositories.users_repository import UsersRepository
from app.schemas.profiles import ProfileResponse
from app.schemas.swipes import SwipeResponse
from app.services.events_service import LikeEventHandler
from app.services.matches_service import MatchesService
from app.services.swipes_service import SwipesService

router = APIRouter(prefix="/swipes", tags=["swipes"])


@router.post("/like/{profile_id}", response_model=SwipeResponse)
async def like_profile(
    profile_id: int,
    telegram_id: Annotated[int, Depends(resolve_telegram_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SwipeResponse:
    service = SwipesService(
        swipes_repository=SwipesRepository(session=session),
        profiles_repository=ProfilesRepository(session=session),
        users_repository=UsersRepository(session=session),
        like_event_handler=LikeEventHandler(),
        matches_service=MatchesService(
            matches_repository=MatchesRepository(session=session),
            users_repository=UsersRepository(session=session),
            session=session,
        ),
        session=session,
    )
    swipe = await service.like(telegram_id=telegram_id, to_profile_id=profile_id)
    return SwipeResponse.model_validate(swipe)


@router.post("/skip/{profile_id}", response_model=SwipeResponse)
async def skip_profile(
    profile_id: int,
    telegram_id: Annotated[int, Depends(resolve_telegram_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SwipeResponse:
    service = SwipesService(
        swipes_repository=SwipesRepository(session=session),
        profiles_repository=ProfilesRepository(session=session),
        users_repository=UsersRepository(session=session),
        like_event_handler=LikeEventHandler(),
        matches_service=MatchesService(
            matches_repository=MatchesRepository(session=session),
            users_repository=UsersRepository(session=session),
            session=session,
        ),
        session=session,
    )
    swipe = await service.skip(telegram_id=telegram_id, to_profile_id=profile_id)
    return SwipeResponse.model_validate(swipe)


@router.get("/history", response_model=list[SwipeResponse])
async def get_swipes_history(
    telegram_id: Annotated[int, Depends(resolve_telegram_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(default=20, ge=1, le=100),
) -> list[SwipeResponse]:
    service = SwipesService(
        swipes_repository=SwipesRepository(session=session),
        profiles_repository=ProfilesRepository(session=session),
        users_repository=UsersRepository(session=session),
        like_event_handler=LikeEventHandler(),
        matches_service=MatchesService(
            matches_repository=MatchesRepository(session=session),
            users_repository=UsersRepository(session=session),
            session=session,
        ),
        session=session,
    )
    swipes = await service.get_history(telegram_id=telegram_id, limit=limit)
    return [SwipeResponse.model_validate(swipe) for swipe in swipes]


@router.get("/likes/outgoing", response_model=list[ProfileResponse])
async def get_outgoing_likes(
    telegram_id: Annotated[int, Depends(resolve_telegram_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(default=20, ge=1, le=100),
) -> list[ProfileResponse]:
    service = SwipesService(
        swipes_repository=SwipesRepository(session=session),
        profiles_repository=ProfilesRepository(session=session),
        users_repository=UsersRepository(session=session),
        like_event_handler=LikeEventHandler(),
        matches_service=MatchesService(
            matches_repository=MatchesRepository(session=session),
            users_repository=UsersRepository(session=session),
            session=session,
        ),
        session=session,
    )
    profiles = await service.get_profiles_liked_by_user(telegram_id=telegram_id, limit=limit)
    return [ProfileResponse.model_validate(profile) for profile in profiles]


@router.get("/likes/incoming", response_model=list[ProfileResponse])
async def get_incoming_likes(
    telegram_id: Annotated[int, Depends(resolve_telegram_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = Query(default=20, ge=1, le=100),
) -> list[ProfileResponse]:
    service = SwipesService(
        swipes_repository=SwipesRepository(session=session),
        profiles_repository=ProfilesRepository(session=session),
        users_repository=UsersRepository(session=session),
        like_event_handler=LikeEventHandler(),
        matches_service=MatchesService(
            matches_repository=MatchesRepository(session=session),
            users_repository=UsersRepository(session=session),
            session=session,
        ),
        session=session,
    )
    profiles = await service.get_profiles_who_liked_user(telegram_id=telegram_id, limit=limit)
    return [ProfileResponse.model_validate(profile) for profile in profiles]
