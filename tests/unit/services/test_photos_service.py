"""Unit tests for PhotosService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.errors import APIError
from app.services.photos_service import PhotosService


@pytest.mark.unit
class TestPhotosService:
    """Tests for PhotosService business logic."""

    @pytest.fixture
    def mock_photos_repository(self):
        """Create mock PhotosRepository."""
        return AsyncMock()

    @pytest.fixture
    def mock_profiles_repository(self):
        """Create mock ProfilesRepository."""
        return AsyncMock()

    @pytest.fixture
    def mock_users_repository(self):
        """Create mock UsersRepository."""
        return AsyncMock()

    @pytest.fixture
    def mock_storage(self):
        """Create mock MinioStorage."""
        return AsyncMock()

    @pytest.fixture
    def mock_session(self):
        """Create mock AsyncSession."""
        return AsyncMock()

    @pytest.fixture
    def service(
        self,
        mock_photos_repository,
        mock_profiles_repository,
        mock_users_repository,
        mock_storage,
        mock_session,
    ):
        """Create PhotosService with mocked dependencies."""
        return PhotosService(
            photos_repository=mock_photos_repository,
            profiles_repository=mock_profiles_repository,
            users_repository=mock_users_repository,
            storage=mock_storage,
            session=mock_session,
        )

    @pytest.mark.asyncio
    async def test_get_user_profile_success(
        self, service, mock_users_repository, mock_profiles_repository
    ):
        """Test getting user profile for photo operations."""
        # Arrange
        telegram_id = 123456789
        user = MagicMock(id=1, telegram_id=telegram_id)
        profile = MagicMock(id=5, user_id=1)

        mock_users_repository.get_by_telegram_id.return_value = user
        mock_profiles_repository.get_by_user_id.return_value = profile

        # Act
        result_user, result_profile = await service._get_user_profile(telegram_id)

        # Assert
        assert result_user.id == 1
        assert result_profile.id == 5

    @pytest.mark.asyncio
    async def test_get_user_profile_user_not_found(self, service, mock_users_repository):
        """Test getting profile for non-existent user."""
        # Arrange
        telegram_id = 999999999
        mock_users_repository.get_by_telegram_id.return_value = None

        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            await service._get_user_profile(telegram_id)

        assert exc_info.value.code == "user_not_found"

    @pytest.mark.asyncio
    async def test_get_user_profile_profile_not_created(
        self, service, mock_users_repository, mock_profiles_repository
    ):
        """Test getting profile when user hasn't created one yet."""
        # Arrange
        telegram_id = 123456789
        user = MagicMock(id=1)

        mock_users_repository.get_by_telegram_id.return_value = user
        mock_profiles_repository.get_by_user_id.return_value = None

        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            await service._get_user_profile(telegram_id)

        assert exc_info.value.code == "profile_not_found"

    @pytest.mark.asyncio
    async def test_upload_photo_invalid_content_type(
        self, service, mock_users_repository, mock_profiles_repository
    ):
        """Test upload with invalid content type."""
        # Arrange
        telegram_id = 123456789
        user = MagicMock(id=1)
        profile = MagicMock(id=5)

        mock_users_repository.get_by_telegram_id.return_value = user
        mock_profiles_repository.get_by_user_id.return_value = profile

        # Create mock file with invalid content type
        mock_file = MagicMock()
        mock_file.content_type = "application/pdf"  # Invalid!
        mock_file.filename = "photo.pdf"

        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            await service.upload_photo(telegram_id, mock_file, None)

        assert exc_info.value.code == "photo_content_type_not_allowed"
        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_upload_photo_invalid_extension(
        self, service, mock_users_repository, mock_profiles_repository
    ):
        """Test upload with invalid file extension."""
        # Arrange
        telegram_id = 123456789
        user = MagicMock(id=1)
        profile = MagicMock(id=5)

        mock_users_repository.get_by_telegram_id.return_value = user
        mock_profiles_repository.get_by_user_id.return_value = profile

        # Create mock file with valid content type but invalid extension
        mock_file = MagicMock()
        mock_file.content_type = "image/jpeg"
        mock_file.filename = "photo.txt"  # Invalid extension!

        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            await service.upload_photo(telegram_id, mock_file, None)

        assert exc_info.value.code == "photo_extension_not_allowed"

    @pytest.mark.asyncio
    async def test_delete_photo_success(
        self,
        service,
        mock_users_repository,
        mock_profiles_repository,
        mock_photos_repository,
        mock_storage,
        mock_session,
    ):
        """Test successful photo deletion."""
        # Arrange
        telegram_id = 123456789
        photo_id = 10
        user = MagicMock(id=1, telegram_id=telegram_id)
        profile = MagicMock(id=5, user_id=1)
        photo = MagicMock(
            id=photo_id, profile_id=5, photo_url="https://minio.example.com/photo.jpg"
        )

        mock_users_repository.get_by_telegram_id.return_value = user
        mock_profiles_repository.get_by_user_id.return_value = profile
        mock_photos_repository.get_by_id.return_value = photo
        mock_photos_repository.delete_photo.return_value = None

        # Act
        await service.delete_photo(telegram_id, photo_id)

        # Assert
        mock_storage.remove_object_by_url.assert_called_once_with(
            "https://minio.example.com/photo.jpg"
        )
        mock_photos_repository.delete_photo.assert_called_once_with(photo)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_photo_not_found(
        self, service, mock_users_repository, mock_profiles_repository, mock_photos_repository
    ):
        """Test deleting non-existent photo."""
        # Arrange
        telegram_id = 123456789
        photo_id = 9999
        user = MagicMock(id=1)
        profile = MagicMock(id=5)

        mock_users_repository.get_by_telegram_id.return_value = user
        mock_profiles_repository.get_by_user_id.return_value = profile
        mock_photos_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            await service.delete_photo(telegram_id, photo_id)

        assert exc_info.value.code == "photo_not_found"
