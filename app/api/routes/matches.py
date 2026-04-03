from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import resolve_telegram_id
from app.core.database import get_db_session
from app.repositories.matches_repository import MatchesRepository
from app.repositories.users_repository import UsersRepository
from app.schemas.matches import MatchDialogStartedRequest, MatchResponse
from app.services.matches_service import MatchesService

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("", response_model=list[MatchResponse])
async def get_matches(
    telegram_id: Annotated[int, Depends(resolve_telegram_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[MatchResponse]:
    service = MatchesService(
        matches_repository=MatchesRepository(session=session),
        users_repository=UsersRepository(session=session),
        session=session,
    )
    matches = await service.list_matches(telegram_id=telegram_id)
    return [MatchResponse.model_validate(match) for match in matches]


@router.post("/dialog-started", response_model=MatchResponse)
async def mark_dialog_started(
    payload: MatchDialogStartedRequest,
    telegram_id: Annotated[int, Depends(resolve_telegram_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> MatchResponse:
    service = MatchesService(
        matches_repository=MatchesRepository(session=session),
        users_repository=UsersRepository(session=session),
        session=session,
    )
    match = await service.start_dialog(telegram_id=telegram_id, match_id=payload.match_id)
    return MatchResponse.model_validate(match)
