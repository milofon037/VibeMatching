from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import resolve_telegram_id
from app.core.database import get_db_session
from app.repositories.profiles_repository import ProfilesRepository
from app.repositories.swipes_repository import SwipesRepository
from app.repositories.matches_repository import MatchesRepository
from app.repositories.users_repository import UsersRepository
from app.schemas.swipes import SwipeRequest, SwipeResponse
from app.services.events_service import LikeEventHandler
from app.services.matches_service import MatchesService
from app.services.swipes_service import SwipesService

router = APIRouter(prefix="/swipe", tags=["swipe"])


@router.post("/like", response_model=SwipeResponse)
async def like_profile(
    payload: SwipeRequest,
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
    swipe = await service.like(telegram_id=telegram_id, to_profile_id=payload.to_profile_id)
    return SwipeResponse.model_validate(swipe)


@router.post("/skip", response_model=SwipeResponse)
async def skip_profile(
    payload: SwipeRequest,
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
    swipe = await service.skip(telegram_id=telegram_id, to_profile_id=payload.to_profile_id)
    return SwipeResponse.model_validate(swipe)
