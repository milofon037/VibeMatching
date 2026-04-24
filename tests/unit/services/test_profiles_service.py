"""Unit tests for ProfilesService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.config import settings
from app.core.errors import APIError
from app.models.enums import SearchCityMode
from app.services.profiles_service import ProfilesService
from app.services.ranking_client import RankingServiceUnavailable


@pytest.mark.unit
class TestProfilesService:
    """Tests for ProfilesService business logic."""

    @pytest.fixture
    def mock_profiles_repository(self):
        """Create mock ProfilesRepository."""
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
    def service(self, mock_profiles_repository, mock_users_repository, mock_session):
        """Create ProfilesService with mocked dependencies."""
        return ProfilesService(
            profiles_repository=mock_profiles_repository,
            users_repository=mock_users_repository,
            session=mock_session,
        )

    @pytest.mark.asyncio
    async def test_create_profile_success(
        self, service, mock_users_repository, mock_profiles_repository, mock_session
    ):
        """Test successful profile creation."""
        # Arrange
        telegram_id = 123456789
        user = MagicMock(id=1, telegram_id=telegram_id)
        profile_data = {"name": "John", "age": 25, "gender": "M", "city": "Moscow"}
        profile = MagicMock(id=1, user_id=1, **profile_data)

        mock_users_repository.get_by_telegram_id.return_value = user
        mock_profiles_repository.get_by_user_id.return_value = None
        mock_profiles_repository.create_profile.return_value = profile

        # Act
        result = await service.create_profile(telegram_id, profile_data)

        # Assert
        assert result.id == 1
        assert result.user_id == 1
        mock_profiles_repository.create_profile.assert_called_once_with(user_id=1, **profile_data)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_profile_user_not_found(self, service, mock_users_repository):
        """Test creating profile for non-existent user."""
        # Arrange
        telegram_id = 999999999
        profile_data = {"name": "John", "age": 25, "gender": "M"}
        mock_users_repository.get_by_telegram_id.return_value = None

        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            await service.create_profile(telegram_id, profile_data)

        assert exc_info.value.code == "user_not_found"
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_create_profile_already_exists(
        self, service, mock_users_repository, mock_profiles_repository
    ):
        """Test that user can only have one active profile."""
        # Arrange
        telegram_id = 123456789
        user = MagicMock(id=1, telegram_id=telegram_id)
        existing_profile = MagicMock(id=1, user_id=1)
        profile_data = {"name": "John", "age": 25, "gender": "M"}

        mock_users_repository.get_by_telegram_id.return_value = user
        mock_profiles_repository.get_by_user_id.return_value = existing_profile

        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            await service.create_profile(telegram_id, profile_data)

        assert exc_info.value.code == "profile_already_exists"
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_get_my_profile_success(
        self, service, mock_users_repository, mock_profiles_repository
    ):
        """Test getting user's own profile."""
        # Arrange
        telegram_id = 123456789
        user = MagicMock(id=1, telegram_id=telegram_id)
        profile = MagicMock(id=1, user_id=1)
        profile.name = "John"  # Set attribute directly

        mock_users_repository.get_by_telegram_id.return_value = user
        mock_profiles_repository.get_by_user_id.return_value = profile

        # Act
        result = await service.get_my_profile(telegram_id)

        # Assert
        assert result.id == 1
        assert result.name == "John"

    @pytest.mark.asyncio
    async def test_get_my_profile_not_found(
        self, service, mock_users_repository, mock_profiles_repository
    ):
        """Test getting profile when it doesn't exist."""
        # Arrange
        telegram_id = 123456789
        user = MagicMock(id=1, telegram_id=telegram_id)

        mock_users_repository.get_by_telegram_id.return_value = user
        mock_profiles_repository.get_by_user_id.return_value = None

        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            await service.get_my_profile(telegram_id)

        assert exc_info.value.code == "profile_not_found"
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_profile_success(
        self, service, mock_users_repository, mock_profiles_repository, mock_session
    ):
        """Test updating profile."""
        # Arrange
        telegram_id = 123456789
        user = MagicMock(id=1)
        old_profile = MagicMock(id=1, user_id=1)
        updated_profile = MagicMock(id=1, user_id=1)
        updated_profile.name = "Jane"
        updated_profile.age = 26
        profile_data = {"name": "Jane", "age": 26}

        mock_users_repository.get_by_telegram_id.return_value = user
        mock_profiles_repository.get_by_user_id.return_value = old_profile
        mock_profiles_repository.update_profile.return_value = updated_profile

        # Act
        result = await service.update_profile(telegram_id, profile_data)

        # Assert
        assert result.name == "Jane"
        assert result.age == 26
        mock_profiles_repository.update_profile.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_search_mode_success(
        self, service, mock_users_repository, mock_profiles_repository, mock_session
    ):
        """Test updating search mode."""
        # Arrange
        telegram_id = 123456789
        user = MagicMock(id=1)
        profile = MagicMock(id=1, user_id=1, search_city_mode=SearchCityMode.LOCAL)
        updated_profile = MagicMock(id=1, user_id=1, search_city_mode=SearchCityMode.GLOBAL)

        mock_users_repository.get_by_telegram_id.return_value = user
        mock_profiles_repository.get_by_user_id.return_value = profile
        mock_profiles_repository.update_search_mode.return_value = updated_profile

        # Act
        result = await service.update_search_mode(telegram_id, SearchCityMode.GLOBAL)

        # Assert
        assert result.search_city_mode == SearchCityMode.GLOBAL
        mock_profiles_repository.update_search_mode.assert_called_once_with(
            profile,
            search_city_mode=SearchCityMode.GLOBAL,
        )
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_feed_profile_not_created(
        self, service, mock_users_repository, mock_profiles_repository
    ):
        """Test that feed requires user to have a profile."""
        # Arrange
        telegram_id = 123456789
        user = MagicMock(id=1)

        mock_users_repository.get_by_telegram_id.return_value = user
        mock_profiles_repository.get_by_user_id.return_value = None

        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            await service.get_feed(telegram_id)

        assert exc_info.value.code == "profile_not_found"

    @pytest.mark.asyncio
    async def test_get_feed_invalid_limit(
        self, service, mock_users_repository, mock_profiles_repository
    ):
        """Test that negative feed limit raises error."""
        # Arrange
        telegram_id = 123456789
        user = MagicMock(id=1)
        profile = MagicMock(id=1, user_id=1)

        mock_users_repository.get_by_telegram_id.return_value = user
        mock_profiles_repository.get_by_user_id.return_value = profile

        # Act & Assert
        with pytest.raises(APIError) as exc_info:
            await service.get_feed(telegram_id, limit=-1)

        assert exc_info.value.code == "feed_limit_invalid"

    @pytest.mark.asyncio
    async def test_get_feed_uses_ranking_service_order_when_enabled(self, monkeypatch):
        """Feed should follow ranking service order when feature is enabled."""
        telegram_id = 123456789
        user = MagicMock(id=1)
        my_profile = MagicMock(id=100, user_id=1, interests_catalog=[MagicMock(id=7)])
        candidate_1 = MagicMock(id=11, user_id=2, interests_catalog=[MagicMock(id=7)])
        candidate_2 = MagicMock(id=22, user_id=3, interests_catalog=[MagicMock(id=8)])

        profiles_repository = AsyncMock()
        users_repository = AsyncMock()
        ratings_repository = AsyncMock()
        ranking_client = AsyncMock()
        feed_cache_service = AsyncMock()
        session = AsyncMock()

        users_repository.get_by_telegram_id.return_value = user
        profiles_repository.get_by_user_id.return_value = my_profile
        profiles_repository.get_feed_profiles.return_value = [candidate_1, candidate_2]
        profiles_repository.get_viewed_profile_ids.return_value = []
        ratings_repository.get_base_ranks_by_user_ids.return_value = {2: 0.4, 3: 0.9}
        ranking_client.rank_feed.return_value = [22, 11]
        feed_cache_service.get_cached_profile_ids.return_value = []

        service = ProfilesService(
            profiles_repository=profiles_repository,
            users_repository=users_repository,
            session=session,
            ratings_repository=ratings_repository,
            ranking_client=ranking_client,
            feed_cache_service=feed_cache_service,
        )

        monkeypatch.setattr(settings, "ranking_service_enabled", True)
        monkeypatch.setattr(settings, "feed_cache_enabled", True)
        monkeypatch.setattr(settings, "feed_cache_batch_size", 10)

        result = await service.get_feed(telegram_id=telegram_id, limit=2)

        assert [item.id for item in result] == [22, 11]
        ranking_client.rank_feed.assert_called_once()
        feed_cache_service.replace_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_feed_fallbacks_to_sql_when_ranking_unavailable(self, monkeypatch):
        """Feed should keep SQL order when ranking service is unavailable."""
        telegram_id = 123456789
        user = MagicMock(id=1)
        my_profile = MagicMock(id=100, user_id=1, interests_catalog=[MagicMock(id=7)])
        candidate_1 = MagicMock(id=11, user_id=2, interests_catalog=[MagicMock(id=7)])
        candidate_2 = MagicMock(id=22, user_id=3, interests_catalog=[MagicMock(id=8)])

        profiles_repository = AsyncMock()
        users_repository = AsyncMock()
        ratings_repository = AsyncMock()
        ranking_client = AsyncMock()
        feed_cache_service = AsyncMock()
        session = AsyncMock()

        users_repository.get_by_telegram_id.return_value = user
        profiles_repository.get_by_user_id.return_value = my_profile
        profiles_repository.get_feed_profiles.return_value = [candidate_1, candidate_2]
        profiles_repository.get_viewed_profile_ids.return_value = []
        ratings_repository.get_base_ranks_by_user_ids.return_value = {2: 0.4, 3: 0.9}
        ranking_client.rank_feed.side_effect = RankingServiceUnavailable("request_failed")
        feed_cache_service.get_cached_profile_ids.return_value = []

        service = ProfilesService(
            profiles_repository=profiles_repository,
            users_repository=users_repository,
            session=session,
            ratings_repository=ratings_repository,
            ranking_client=ranking_client,
            feed_cache_service=feed_cache_service,
        )

        monkeypatch.setattr(settings, "ranking_service_enabled", True)
        monkeypatch.setattr(settings, "feed_cache_enabled", True)
        monkeypatch.setattr(settings, "feed_cache_batch_size", 10)

        result = await service.get_feed(telegram_id=telegram_id, limit=2)

        assert [item.id for item in result] == [11, 22]

    @pytest.mark.asyncio
    async def test_get_feed_uses_redis_cache_hit(self, monkeypatch):
        """Feed should return cached queue when enough cached ids are available."""
        telegram_id = 123456789
        user = MagicMock(id=1)
        my_profile = MagicMock(id=100, user_id=1, interests_catalog=[])
        cached_profile_1 = MagicMock(id=11, user_id=2, interests_catalog=[])
        cached_profile_2 = MagicMock(id=22, user_id=3, interests_catalog=[])

        profiles_repository = AsyncMock()
        users_repository = AsyncMock()
        feed_cache_service = AsyncMock()
        session = AsyncMock()

        users_repository.get_by_telegram_id.return_value = user
        profiles_repository.get_by_user_id.return_value = my_profile
        profiles_repository.get_by_ids.return_value = [cached_profile_1, cached_profile_2]
        feed_cache_service.get_cached_profile_ids.return_value = [11, 22]

        service = ProfilesService(
            profiles_repository=profiles_repository,
            users_repository=users_repository,
            session=session,
            feed_cache_service=feed_cache_service,
        )

        monkeypatch.setattr(settings, "feed_cache_enabled", True)

        result = await service.get_feed(telegram_id=telegram_id, limit=2)

        assert [item.id for item in result] == [11, 22]
        feed_cache_service.consume.assert_called_once_with(user_id=1, count=2)
        profiles_repository.get_feed_profiles.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_feed_refills_cache_with_next_batch(self, monkeypatch):
        """Feed should cache the next 10 ranked profiles after responding."""
        telegram_id = 123456789
        user = MagicMock(id=1)
        my_profile = MagicMock(id=100, user_id=1, interests_catalog=[])
        candidates = [MagicMock(id=index, user_id=100 + index, interests_catalog=[]) for index in range(1, 13)]

        profiles_repository = AsyncMock()
        users_repository = AsyncMock()
        ranking_client = AsyncMock()
        ratings_repository = AsyncMock()
        feed_cache_service = AsyncMock()
        session = AsyncMock()

        users_repository.get_by_telegram_id.return_value = user
        profiles_repository.get_by_user_id.return_value = my_profile
        profiles_repository.get_feed_profiles.return_value = candidates
        profiles_repository.get_viewed_profile_ids.return_value = []
        ratings_repository.get_base_ranks_by_user_ids.return_value = {
            candidate.user_id: 0.5 for candidate in candidates
        }
        ranking_client.rank_feed.return_value = [candidate.id for candidate in candidates]
        feed_cache_service.get_cached_profile_ids.return_value = []

        service = ProfilesService(
            profiles_repository=profiles_repository,
            users_repository=users_repository,
            session=session,
            ratings_repository=ratings_repository,
            ranking_client=ranking_client,
            feed_cache_service=feed_cache_service,
        )

        monkeypatch.setattr(settings, "ranking_service_enabled", True)
        monkeypatch.setattr(settings, "feed_cache_enabled", True)
        monkeypatch.setattr(settings, "feed_cache_batch_size", 10)

        result = await service.get_feed(telegram_id=telegram_id, limit=2)

        assert [item.id for item in result] == [1, 2]
        feed_cache_service.replace_cache.assert_called_once_with(
            user_id=1,
            profile_ids=[3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        )
