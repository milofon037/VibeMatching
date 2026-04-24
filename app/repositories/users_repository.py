from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UsersRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        query = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> User | None:
        query = select(User).where(User.id == user_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_user(self, telegram_id: int, referral_code: str | None = None) -> User:
        user = User(telegram_id=telegram_id, referral_code=referral_code)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update_last_active(self, user: User) -> User:
        user.last_active_at = datetime.now(tz=UTC)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def count_referred_users(
        self,
        inviter_user_id: int,
        inviter_referral_code: str | None = None,
    ) -> int:
        filters = [User.invited_by == inviter_user_id]
        if inviter_referral_code:
            filters.append(User.referral_code == inviter_referral_code)

        query = select(func.count(User.id)).where(or_(*filters)).where(User.id != inviter_user_id)
        result = await self.session.execute(query)
        return int(result.scalar_one() or 0)
