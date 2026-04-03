from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.errors import APIError
from app.repositories.matches_repository import MatchesRepository
from app.repositories.users_repository import UsersRepository


class MatchesService:
    def __init__(
        self,
        matches_repository: MatchesRepository,
        users_repository: UsersRepository,
        session: AsyncSession,
    ) -> None:
        self.matches_repository = matches_repository
        self.users_repository = users_repository
        self.session = session

    async def _get_user_by_telegram_id(self, telegram_id: int):
        user = await self.users_repository.get_by_telegram_id(telegram_id)
        if not user:
            raise APIError(
                code="user_not_found",
                message="User is not registered.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return user

    async def ensure_match(self, user_a_id: int, user_b_id: int):
        existing = await self.matches_repository.get_by_pair(user_a_id, user_b_id)
        if existing:
            return existing

        try:
            created = await self.matches_repository.create_match(user_a_id, user_b_id)
            await self.session.flush()
            return created
        except IntegrityError:
            await self.session.rollback()
            fallback = await self.matches_repository.get_by_pair(user_a_id, user_b_id)
            if fallback:
                return fallback
            raise APIError(
                code="match_conflict",
                message="Could not create match due to conflicting data.",
                status_code=status.HTTP_409_CONFLICT,
            )

    async def list_matches(self, telegram_id: int):
        user = await self._get_user_by_telegram_id(telegram_id)
        return await self.matches_repository.list_for_user(user.id)

    async def start_dialog(self, telegram_id: int, match_id: int):
        user = await self._get_user_by_telegram_id(telegram_id)
        match = await self.matches_repository.get_for_user_by_id(user.id, match_id)
        if not match:
            raise APIError(
                code="match_not_found",
                message="Match not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if match.dialog_started:
            return match

        updated = await self.matches_repository.mark_dialog_started(match)
        await self.session.commit()
        return updated
