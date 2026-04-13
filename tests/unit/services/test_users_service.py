"""Unit tests for UsersService."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.errors import APIError
from app.services.users_service import UsersService


@pytest.mark.unit
class TestUsersService:
    """Tests for UsersService business logic."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock UsersRepository."""
        return AsyncMock()

    @pytest.fixture
    def mock_session(self):
        """Create mock AsyncSession."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repository, mock_session):
        """Create UsersService with mocked dependencies."""
        return UsersService(
            repository=mock_repository,
            session=mock_session,
        )

    @pytest.mark.asyncio
    async def test_register_user_success(self, service, mock_repository, mock_session):
        """Test successful user registration."""
        # Arrange
        telegram_id = 123456789
        mock_repository.get_by_telegram_id.return_value = None
        mock_user = MagicMock(id=1, telegram_id=telegram_id)
        mock_repository.create_user.return_value = mock_user

        # Act
        result = await service.register_user(telegram_id)

        # Assert
        assert result.id == 1
        assert result.telegram_id == telegram_id
        mock_repository.get_by_telegram_id.assert_called_once_with(telegram_id)
        mock_repository.create_user.assert_called_once_with(
            telegram_id=telegram_id,
            referral_code=None,
        )
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_idempotent(self, service, mock_repository, mock_session):
        """Test that registering same user twice is idempotent."""
        # Arrange
        telegram_id = 123456789
        existing_user = MagicMock(id=1, telegram_id=telegram_id)
        mock_repository.get_by_telegram_id.return_value = existing_user

        # Act
        result = await service.register_user(telegram_id)

        # Assert
        assert result.id == 1
        mock_repository.create_user.assert_not_called()
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_register_user_with_referral_code(self, service, mock_repository, mock_session):
        """Test user registration with referral code."""
        # Arrange
        telegram_id = 123456789
        referral_code = "REF_CODE_123"
        mock_repository.get_by_telegram_id.return_value = None
        mock_user = MagicMock(id=1, telegram_id=telegram_id, referral_code=referral_code)
        mock_repository.create_user.return_value = mock_user

        # Act
        result = await service.register_user(telegram_id, referral_code=referral_code)

        # Assert
        assert result.referral_code == referral_code
        mock_repository.create_user.assert_called_once_with(
            telegram_id=telegram_id,
            referral_code=referral_code,
        )

    @pytest.mark.asyncio
    async def test_register_user_integrity_error_recovery(
        self, service, mock_repository, mock_session
    ):
        """Test recovery from IntegrityError during registration."""
        # Arrange
        telegram_id = 123456789
        mock_repository.get_by_telegram_id.side_effect = [
            None,
            MagicMock(id=1, telegram_id=telegram_id),
        ]
        mock_repository.create_user.side_effect = IntegrityError(
            statement="INSERT INTO users VALUES (...)",
            params={},
            orig=Exception("Unique constraint violation"),
        )

        # Act
        result = await service.register_user(telegram_id)

        # Assert
        assert result.telegram_id == telegram_id
        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, service, mock_repository):
        """Test getting existing user."""
        # Arrange
        telegram_id = 123456789
        mock_user = MagicMock(id=1, telegram_id=telegram_id)
        mock_repository.get_by_telegram_id.return_value = mock_user

        # Act
        result = await service.get_current_user(telegram_id)

        # Assert
        assert result.id == 1
        mock_repository.get_by_telegram_id.assert_called_once_with(telegram_id)

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, service, mock_repository):
        """Test getting non-existent user raises error."""
        # Arrange
        telegram_id = 999999999
        mock_repository.get_by_telegram_id.return_value = None

        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            await service.get_current_user(telegram_id)

        assert exc_info.value.code == "user_not_found"
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_activity_success(self, service, mock_repository, mock_session):
        """Test updating user activity."""
        # Arrange
        telegram_id = 123456789
        existing_user = MagicMock(id=1, telegram_id=telegram_id)
        updated_user = MagicMock(
            id=1, telegram_id=telegram_id, last_active_at="2026-04-10T10:00:00"
        )

        mock_repository.get_by_telegram_id.return_value = existing_user
        mock_repository.update_last_active.return_value = updated_user

        # Act
        result = await service.update_activity(telegram_id)

        # Assert
        assert result.id == 1
        mock_repository.update_last_active.assert_called_once_with(existing_user)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_activity_user_not_found(self, service, mock_repository):
        """Test updating activity for non-existent user."""
        # Arrange
        telegram_id = 999999999
        mock_repository.get_by_telegram_id.return_value = None

        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            await service.update_activity(telegram_id)

        assert exc_info.value.code == "user_not_found"
        mock_repository.update_last_active.assert_not_called()
