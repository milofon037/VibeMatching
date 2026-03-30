from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.errors import APIError
from app.repositories.users_repository import UsersRepository


class UsersService:
    def __init__(self, repository: UsersRepository, session: AsyncSession) -> None:
        self.repository = repository
        self.session = session

    async def register_user(self, telegram_id: int, referral_code: str | None = None):
        existing = await self.repository.get_by_telegram_id(telegram_id)
        if existing:
            return existing

        try:
            created = await self.repository.create_user(telegram_id=telegram_id, referral_code=referral_code)
            await self.session.commit()
            return created
        except IntegrityError:
            await self.session.rollback()
            fallback = await self.repository.get_by_telegram_id(telegram_id)
            if fallback:
                return fallback
            raise APIError(
                code="user_conflict",
                message="Could not register user because of a conflicting telegram_id.",
                status_code=status.HTTP_409_CONFLICT,
            )

    async def get_current_user(self, telegram_id: int):
        user = await self.repository.get_by_telegram_id(telegram_id)
        if not user:
            raise APIError(
                code="user_not_found",
                message="User is not registered.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return user

    async def update_activity(self, telegram_id: int):
        user = await self.get_current_user(telegram_id)
        updated = await self.repository.update_last_active(user)
        await self.session.commit()
        return updated
