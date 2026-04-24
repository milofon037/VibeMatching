from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.repositories.interests_repository import InterestsRepository
from app.repositories.profiles_repository import ProfilesRepository
from app.repositories.users_repository import UsersRepository
from app.schemas.interests import InterestResponse
from app.services.events_service import LikeEventHandler
from app.services.interests_service import InterestsService

router = APIRouter(prefix="/interests", tags=["interests"])


@router.get("", response_model=list[InterestResponse])
async def list_interests(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[InterestResponse]:
    service = InterestsService(
        interests_repository=InterestsRepository(session=session),
        profiles_repository=ProfilesRepository(session=session),
        users_repository=UsersRepository(session=session),
        event_handler=LikeEventHandler(),
        session=session,
    )
    interests = await service.list_interests()
    return [InterestResponse.model_validate(interest) for interest in interests]
