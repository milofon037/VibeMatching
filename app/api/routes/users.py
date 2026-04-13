from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import resolve_telegram_id
from app.core.database import get_db_session
from app.repositories.users_repository import UsersRepository
from app.schemas.users import UserActivityResponse, UserRegisterRequest, UserResponse
from app.services.users_service import UsersService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserResponse)
async def register_user(
    payload: UserRegisterRequest, session: Annotated[AsyncSession, Depends(get_db_session)]
) -> UserResponse:
    repository = UsersRepository(session=session)
    service = UsersService(repository=repository, session=session)
    user = await service.register_user(
        telegram_id=payload.telegram_id, referral_code=payload.referral_code
    )
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def get_me(
    telegram_id: Annotated[int, Depends(resolve_telegram_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserResponse:
    repository = UsersRepository(session=session)
    service = UsersService(repository=repository, session=session)
    user = await service.get_current_user(telegram_id=telegram_id)
    return UserResponse.model_validate(user)


@router.patch("/activity", response_model=UserActivityResponse)
async def update_activity(
    telegram_id: Annotated[int, Depends(resolve_telegram_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserActivityResponse:
    repository = UsersRepository(session=session)
    service = UsersService(repository=repository, session=session)
    user = await service.update_activity(telegram_id=telegram_id)
    return UserActivityResponse(user_id=user.id, last_active_at=user.last_active_at)
