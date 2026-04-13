"""Unit tests for MatchesService."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.errors import APIError
from app.services.matches_service import MatchesService


@pytest.mark.unit
class TestMatchesService:
    """Tests for MatchesService business logic."""

    @pytest.fixture
    def mock_matches_repository(self):
        """Create mock MatchesRepository."""
        return AsyncMock()

    @pytest.fixture
    def mock_users_repository(self):
        """Create mock UsersRepository."""
        return AsyncMock()

    @pytest.fixture
    def mock_session(self):
        """Create mock AsyncSession."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_matches_repository, mock_users_repository, mock_session):
        """Create MatchesService with mocked dependencies."""
        return MatchesService(
            matches_repository=mock_matches_repository,
            users_repository=mock_users_repository,
            session=mock_session,
        )

    @pytest.mark.asyncio
    async def test_ensure_match_new_match(self, service, mock_matches_repository, mock_session):
        """Test creating a new match when it doesn't exist."""
        # Arrange
        user_a_id = 1
        user_b_id = 2
        match = MagicMock(id=1, user_a_id=user_a_id, user_b_id=user_b_id)

        mock_matches_repository.get_by_pair.return_value = None
        mock_matches_repository.create_match.return_value = match

        # Act
        result = await service.ensure_match(user_a_id, user_b_id)

        # Assert
        assert result.id == 1
        assert result.user_a_id == user_a_id
        mock_matches_repository.create_match.assert_called_once_with(user_a_id, user_b_id)
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_match_already_exists(
        self, service, mock_matches_repository, mock_session
    ):
        """Test that existing match is returned without creating new one."""
        # Arrange
        user_a_id = 1
        user_b_id = 2
        existing_match = MagicMock(id=1, user_a_id=user_a_id, user_b_id=user_b_id)

        mock_matches_repository.get_by_pair.return_value = existing_match

        # Act
        result = await service.ensure_match(user_a_id, user_b_id)

        # Assert
        assert result.id == 1
        mock_matches_repository.create_match.assert_not_called()
        mock_session.flush.assert_not_called()

    @pytest.mark.asyncio
    async def test_ensure_match_integrity_error_recovery(
        self, service, mock_matches_repository, mock_session
    ):
        """Test recovery from integrity error during match creation."""
        # Arrange
        user_a_id = 1
        user_b_id = 2
        match = MagicMock(id=1, user_a_id=user_a_id, user_b_id=user_b_id)

        mock_matches_repository.get_by_pair.side_effect = [None, match]
        mock_matches_repository.create_match.side_effect = IntegrityError(
            statement="INSERT INTO matches VALUES (...)",
            params={},
            orig=Exception("Unique constraint violation"),
        )

        # Act
        result = await service.ensure_match(user_a_id, user_b_id)

        # Assert
        assert result.id == 1
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_matches_success(
        self, service, mock_users_repository, mock_matches_repository
    ):
        """Test listing user's matches."""
        # Arrange
        telegram_id = 123456789
        user = MagicMock(id=1, telegram_id=telegram_id)
        matches = [
            MagicMock(id=1, user_a_id=1, user_b_id=2),
            MagicMock(id=2, user_a_id=1, user_b_id=3),
        ]

        mock_users_repository.get_by_telegram_id.return_value = user
        mock_matches_repository.list_for_user.return_value = matches

        # Act
        result = await service.list_matches(telegram_id)

        # Assert
        assert len(result) == 2
        assert result[0].id == 1
        mock_matches_repository.list_for_user.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_list_matches_user_not_found(self, service, mock_users_repository):
        """Test listing matches for non-existent user."""
        # Arrange
        telegram_id = 999999999
        mock_users_repository.get_by_telegram_id.return_value = None

        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            await service.list_matches(telegram_id)

        assert exc_info.value.code == "user_not_found"

    @pytest.mark.asyncio
    async def test_list_matches_empty(
        self, service, mock_users_repository, mock_matches_repository
    ):
        """Test listing matches when user has no matches."""
        # Arrange
        telegram_id = 123456789
        user = MagicMock(id=1)

        mock_users_repository.get_by_telegram_id.return_value = user
        mock_matches_repository.list_for_user.return_value = []

        # Act
        result = await service.list_matches(telegram_id)

        # Assert
        assert result == []
