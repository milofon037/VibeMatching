from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.core.config import settings
from app.core.errors import APIError
from app.core.minio_client import MinioStorage
from app.repositories.photos_repository import PhotosRepository
from app.repositories.profiles_repository import ProfilesRepository
from app.repositories.users_repository import UsersRepository


class PhotosService:
    def __init__(
        self,
        photos_repository: PhotosRepository,
        profiles_repository: ProfilesRepository,
        users_repository: UsersRepository,
        storage: MinioStorage,
        session: AsyncSession,
    ) -> None:
        self.photos_repository = photos_repository
        self.profiles_repository = profiles_repository
        self.users_repository = users_repository
        self.storage = storage
        self.session = session

    async def _get_user_profile(self, telegram_id: int):
        user = await self.users_repository.get_by_telegram_id(telegram_id)
        if not user:
            raise APIError(
                code="user_not_found",
                message="User is not registered.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        profile = await self.profiles_repository.get_by_user_id(user.id)
        if not profile:
            raise APIError(
                code="profile_not_found",
                message="Profile is not created yet.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return user, profile

    async def upload_photo(self, telegram_id: int, file: UploadFile, requested_position: int | None):
        _, profile = await self._get_user_profile(telegram_id)
        _ = requested_position

        if file.content_type not in settings.photo_allowed_content_types:
            raise APIError(
                code="photo_content_type_not_allowed",
                message=f"Allowed content types: {', '.join(settings.photo_allowed_content_types)}",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        file_extension = Path(file.filename or "").suffix.lower()
        if not file_extension or file_extension not in settings.photo_allowed_extensions:
            raise APIError(
                code="photo_extension_not_allowed",
                message=f"Allowed extensions: {', '.join(settings.photo_allowed_extensions)}",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        payload = await file.read()
        if len(payload) == 0:
            raise APIError(
                code="photo_empty_file",
                message="Uploaded file is empty.",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        if len(payload) > settings.photo_max_file_size_bytes:
            raise APIError(
                code="photo_too_large",
                message=f"Max allowed file size is {settings.photo_max_file_size_bytes} bytes.",
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        object_name = f"profile_{profile.id}/{uuid4().hex}{file_extension}"
        photo_url = self.storage.upload_bytes(object_name=object_name, payload=payload, content_type=file.content_type)
        existing_photos = await self.photos_repository.get_by_profile_id(profile.id)

        try:
            for existing_photo in existing_photos:
                self.storage.remove_object_by_url(existing_photo.photo_url)
                await self.photos_repository.delete_photo(existing_photo)

            photo = await self.photos_repository.create_photo(profile_id=profile.id, photo_url=photo_url, position=1)
            await self.session.commit()
            return photo
        except IntegrityError:
            await self.session.rollback()
            self.storage.remove_object_by_url(photo_url)
            raise APIError(
                code="photo_update_conflict",
                message="Could not update profile photo.",
                status_code=status.HTTP_409_CONFLICT,
            )

    async def get_profile_photos(self, profile_id: int):
        return await self.photos_repository.get_by_profile_id(profile_id)

    async def get_my_photos(self, telegram_id: int):
        _, profile = await self._get_user_profile(telegram_id)
        return await self.photos_repository.get_by_profile_id(profile.id)

    async def get_photo_by_id(self, photo_id: int):
        photo = await self.photos_repository.get_by_id(photo_id)
        if not photo:
            raise APIError(
                code="photo_not_found",
                message="Photo not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return photo

    async def get_primary_photo_bytes(self, profile_id: int) -> tuple[bytes, str | None] | None:
        photos = await self.photos_repository.get_by_profile_id(profile_id)
        if not photos:
            return None

        primary_photo = sorted(photos, key=lambda photo: photo.position)[0]
        return self.storage.get_object_bytes_by_url(primary_photo.photo_url)

    async def delete_photo(self, telegram_id: int, photo_id: int):
        _, profile = await self._get_user_profile(telegram_id)
        photo = await self.photos_repository.get_by_id(photo_id)
        if not photo:
            raise APIError(
                code="photo_not_found",
                message="Photo not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if photo.profile_id != profile.id:
            raise APIError(
                code="photo_forbidden",
                message="You can delete only your own photos.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        self.storage.remove_object_by_url(photo.photo_url)
        await self.photos_repository.delete_photo(photo)
        await self.session.commit()

    async def set_main_photo(self, telegram_id: int, photo_id: int):
        _, profile = await self._get_user_profile(telegram_id)

        photo = await self.photos_repository.get_by_id(photo_id)
        if not photo:
            raise APIError(
                code="photo_not_found",
                message="Photo not found.",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if photo.profile_id != profile.id:
            raise APIError(
                code="photo_forbidden",
                message="You can modify only your own photos.",
                status_code=status.HTTP_403_FORBIDDEN,
            )

        photos = await self.photos_repository.get_by_profile_id(profile.id)
        for profile_photo in photos:
            profile_photo.position = 1 if profile_photo.id == photo.id else 2

        await self.session.commit()
        await self.session.refresh(photo)
        return photo
