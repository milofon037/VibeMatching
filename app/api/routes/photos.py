from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import resolve_telegram_id
from app.core.database import get_db_session
from app.core.minio_client import MinioStorage
from app.repositories.photos_repository import PhotosRepository
from app.repositories.profiles_repository import ProfilesRepository
from app.repositories.users_repository import UsersRepository
from app.schemas.photos import PhotoDeleteResponse, PhotoResponse, PhotoUploadResponse
from app.services.photos_service import PhotosService

router = APIRouter(prefix="/photos", tags=["photos"])


@router.post("/upload", response_model=PhotoUploadResponse)
async def upload_photo(
    telegram_id: Annotated[int, Depends(resolve_telegram_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    file: UploadFile = File(...),
    position: int | None = Form(default=None),
) -> PhotoUploadResponse:
    service = PhotosService(
        photos_repository=PhotosRepository(session=session),
        profiles_repository=ProfilesRepository(session=session),
        users_repository=UsersRepository(session=session),
        storage=MinioStorage(),
        session=session,
    )
    photo = await service.upload_photo(telegram_id=telegram_id, file=file, requested_position=position)
    return PhotoUploadResponse(photo=PhotoResponse.model_validate(photo))


@router.get("/{profile_id}", response_model=list[PhotoResponse])
async def get_profile_photos(
    profile_id: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[PhotoResponse]:
    service = PhotosService(
        photos_repository=PhotosRepository(session=session),
        profiles_repository=ProfilesRepository(session=session),
        users_repository=UsersRepository(session=session),
        storage=MinioStorage(),
        session=session,
    )
    photos = await service.get_profile_photos(profile_id=profile_id)
    return [PhotoResponse.model_validate(photo) for photo in photos]


@router.delete("/{photo_id}", response_model=PhotoDeleteResponse)
async def delete_photo(
    photo_id: int,
    telegram_id: Annotated[int, Depends(resolve_telegram_id)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> PhotoDeleteResponse:
    service = PhotosService(
        photos_repository=PhotosRepository(session=session),
        profiles_repository=ProfilesRepository(session=session),
        users_repository=UsersRepository(session=session),
        storage=MinioStorage(),
        session=session,
    )
    await service.delete_photo(telegram_id=telegram_id, photo_id=photo_id)
    return PhotoDeleteResponse(photo_id=photo_id)
