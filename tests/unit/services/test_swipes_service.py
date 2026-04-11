"""Unit tests for SwipesService."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.errors import APIError
from app.models.enums import SwipeAction
from app.services.swipes_service import SwipesService


@pytest.mark.unit
class TestSwipesService:
    """Tests for SwipesService business logic."""

    @pytest.fixture
    def mock_swipes_repository(self):
        """Create mock SwipesRepository."""
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
    def mock_like_event_handler(self):
        """Create mock LikeEventHandler."""
        return AsyncMock()

    @pytest.fixture
    def mock_matches_service(self):
        """Create mock MatchesService."""
        return AsyncMock()

    @pytest.fixture
    def mock_session(self):
        """Create mock AsyncSession."""
        return AsyncMock()

    @pytest.fixture
    def service(
        self,
        mock_swipes_repository,
        mock_profiles_repository,
        mock_users_repository,
        mock_like_event_handler,
        mock_matches_service,
        mock_session,
    ):
        """Create SwipesService with mocked dependencies."""
        return SwipesService(
            swipes_repository=mock_swipes_repository,
            profiles_repository=mock_profiles_repository,
            users_repository=mock_users_repository,
            like_event_handler=mock_like_event_handler,
            matches_service=mock_matches_service,
            session=mock_session,
        )

    @pytest.mark.asyncio
    async def test_like_success(
        self,
        service,
        mock_users_repository,
        mock_profiles_repository,
        mock_swipes_repository,
        mock_session,
    ):
        """Test successful like action."""
        # Arrange
        from_telegram_id = 123456789
        to_profile_id = 5
        from_user = MagicMock(id=1, telegram_id=from_telegram_id)
        to_profile = MagicMock(id=to_profile_id, user_id=2)
        swipe = MagicMock(id=1, from_user_id=1, to_profile_id=to_profile_id, action=SwipeAction.LIKE)

        mock_users_repository.get_by_telegram_id.return_value = from_user
        mock_profiles_repository.get_by_id.return_value = to_profile
        mock_swipes_repository.get_by_user_and_profile.return_value = None
        mock_swipes_repository.create_swipe.return_value = swipe

        # Act
        result = await service._create_swipe(from_telegram_id, to_profile_id, SwipeAction.LIKE)

        # Assert
        assert result.action == SwipeAction.LIKE
        mock_swipes_repository.create_swipe.assert_called_once()
        # Check that commit was called at least once
        assert mock_session.commit.call_count >= 1

    @pytest.mark.asyncio
    async def test_skip_success(
        self,
        service,
        mock_users_repository,
        mock_profiles_repository,
        mock_swipes_repository,
        mock_session,
    ):
        """Test successful skip action."""
        # Arrange
        from_telegram_id = 123456789
        to_profile_id = 5
        from_user = MagicMock(id=1)
        to_profile = MagicMock(id=to_profile_id, user_id=2)
        swipe = MagicMock(id=1, from_user_id=1, to_profile_id=to_profile_id, action=SwipeAction.SKIP)

        mock_users_repository.get_by_telegram_id.return_value = from_user
        mock_profiles_repository.get_by_id.return_value = to_profile
        mock_swipes_repository.get_by_user_and_profile.return_value = None
        mock_swipes_repository.create_swipe.return_value = swipe

        # Act
        result = await service._create_swipe(from_telegram_id, to_profile_id, SwipeAction.SKIP)

        # Assert
        assert result.action == SwipeAction.SKIP

    @pytest.mark.asyncio
    async def test_swipe_target_profile_not_found(self, service, mock_users_repository, mock_profiles_repository):
        """Test swiping non-existent profile."""
        # Arrange
        from_telegram_id = 123456789
        to_profile_id = 9999
        from_user = MagicMock(id=1)

        mock_users_repository.get_by_telegram_id.return_value = from_user
        mock_profiles_repository.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            await service._create_swipe(from_telegram_id, to_profile_id, SwipeAction.LIKE)

        assert exc_info.value.code == "target_profile_not_found"
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_swipe_self_forbidden(self, service, mock_users_repository, mock_profiles_repository):
        """Test that user cannot swipe their own profile."""
        # Arrange
        from_telegram_id = 123456789
        user_id = 1
        to_profile_id = 5
        from_user = MagicMock(id=user_id)
        to_profile = MagicMock(id=to_profile_id, user_id=user_id)  # Same user!

        mock_users_repository.get_by_telegram_id.return_value = from_user
        mock_profiles_repository.get_by_id.return_value = to_profile

        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            await service._create_swipe(from_telegram_id, to_profile_id, SwipeAction.LIKE)

        assert exc_info.value.code == "swipe_self_forbidden"
        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_swipe_duplicate_prevented(
        self,
        service,
        mock_users_repository,
        mock_profiles_repository,
        mock_swipes_repository,
    ):
        """Test that duplicate swipes are prevented."""
        # Arrange
        from_telegram_id = 123456789
        to_profile_id = 5
        from_user = MagicMock(id=1)
        to_profile = MagicMock(id=to_profile_id, user_id=2)
        existing_swipe = MagicMock(id=1, action=SwipeAction.LIKE)

        mock_users_repository.get_by_telegram_id.return_value = from_user
        mock_profiles_repository.get_by_id.return_value = to_profile
        mock_swipes_repository.get_by_user_and_profile.return_value = existing_swipe

        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            await service._create_swipe(from_telegram_id, to_profile_id, SwipeAction.LIKE)

        assert exc_info.value.code == "swipe_already_exists"
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_swipe_user_not_found(self, service, mock_users_repository):
        """Test swiping with non-existent user."""
        # Arrange
        from_telegram_id = 999999999
        to_profile_id = 5

        mock_users_repository.get_by_telegram_id.return_value = None

        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            await service._create_swipe(from_telegram_id, to_profile_id, SwipeAction.LIKE)

        assert exc_info.value.code == "user_not_found"

    @pytest.mark.asyncio
    async def test_swipe_integrity_error(
        self,
        service,
        mock_users_repository,
        mock_profiles_repository,
        mock_swipes_repository,
        mock_session,
    ):
        """Test handling of database integrity error."""
        # Arrange
        from_telegram_id = 123456789
        to_profile_id = 5
        from_user = MagicMock(id=1)
        to_profile = MagicMock(id=to_profile_id, user_id=2)

        mock_users_repository.get_by_telegram_id.return_value = from_user
        mock_profiles_repository.get_by_id.return_value = to_profile
        mock_swipes_repository.get_by_user_and_profile.return_value = None
        mock_swipes_repository.create_swipe.side_effect = IntegrityError(
            statement="INSERT INTO swipes VALUES (...)",
            params={},
            orig=Exception("Unique constraint violation"),
        )

        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            await service._create_swipe(from_telegram_id, to_profile_id, SwipeAction.LIKE)

        assert exc_info.value.code == "swipe_conflict"
        mock_session.rollback.assert_called_once()
