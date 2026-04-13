from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.photo import Photo


class PhotosRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, photo_id: int) -> Photo | None:
        query = select(Photo).where(Photo.id == photo_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_profile_id(self, profile_id: int) -> list[Photo]:
        query = select(Photo).where(Photo.profile_id == profile_id).order_by(Photo.position.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_profile_id(self, profile_id: int) -> int:
        query = select(func.count(Photo.id)).where(Photo.profile_id == profile_id)
        result = await self.session.execute(query)
        return int(result.scalar_one())

    async def get_next_position(self, profile_id: int) -> int:
        query = select(func.coalesce(func.max(Photo.position), 0)).where(
            Photo.profile_id == profile_id
        )
        result = await self.session.execute(query)
        max_position = int(result.scalar_one())
        return max_position + 1

    async def create_photo(self, profile_id: int, photo_url: str, position: int) -> Photo:
        photo = Photo(profile_id=profile_id, photo_url=photo_url, position=position)
        self.session.add(photo)
        await self.session.flush()
        await self.session.refresh(photo)
        return photo

    async def delete_photo(self, photo: Photo) -> None:
        await self.session.delete(photo)
        await self.session.flush()
