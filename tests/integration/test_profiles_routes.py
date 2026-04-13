"""Integration tests for Profiles API routes."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestProfilesRoutes:
    """Integration tests for /profiles endpoints."""

    async def _register_user(self, async_client: AsyncClient, telegram_id: int) -> dict:
        """Helper to register a user. Returns both the user data and telegram_id."""
        response = await async_client.post(
            "/api/v1/users/register", json={"telegram_id": telegram_id}
        )
        assert response.status_code == 200
        return {**response.json(), "telegram_id": telegram_id}

    @pytest.mark.asyncio
    async def test_create_profile_success(self, async_client: AsyncClient, test_db):
        """Test successful profile creation."""
        # Arrange - register user first
        user = await self._register_user(async_client, 123456789)
        telegram_id = user["telegram_id"]

        profile_data = {
            "name": "John Doe",
            "age": 25,
            "gender": "male",
            "city": "Moscow",
        }

        # Act
        response = await async_client.post(
            "/api/v1/profiles/create",
            json=profile_data,
            headers={"X-Telegram-Id": str(telegram_id)},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "John Doe"
        assert data["age"] == 25
        assert data["gender"] == "male"
        assert data["city"] == "Moscow"

    @pytest.mark.asyncio
    async def test_create_profile_user_not_found(self, async_client: AsyncClient):
        """Test creating profile for non-existent user."""
        # Arrange
        profile_data = {
            "name": "John",
            "age": 25,
            "gender": "male",
            "city": "Moscow",
        }

        # Act
        response = await async_client.post(
            "/api/v1/profiles/create",
            json=profile_data,
            headers={"X-Telegram-Id": "99999"},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_my_profile_success(self, async_client: AsyncClient):
        """Test getting user's own profile."""
        # Arrange - register and create profile
        user = await self._register_user(async_client, 222222)
        telegram_id = user["telegram_id"]

        profile_data = {
            "name": "Jane",
            "age": 28,
            "gender": "female",
            "city": "SPB",
        }
        await async_client.post(
            "/api/v1/profiles/create",
            json=profile_data,
            headers={"X-Telegram-Id": str(telegram_id)},
        )

        # Act
        response = await async_client.get(
            "/api/v1/profiles/me", headers={"X-Telegram-Id": str(telegram_id)}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Jane"
        assert data["age"] == 28

    @pytest.mark.asyncio
    async def test_get_my_profile_not_created(self, async_client: AsyncClient):
        """Test getting profile when it doesn't exist."""
        # Arrange - register user but don't create profile
        user = await self._register_user(async_client, 333333)
        telegram_id = user["telegram_id"]

        # Act
        response = await async_client.get(
            "/api/v1/profiles/me", headers={"X-Telegram-Id": str(telegram_id)}
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_profile_success(self, async_client: AsyncClient):
        """Test updating profile."""
        # Arrange - register and create profile
        user = await self._register_user(async_client, 444444)
        telegram_id = user["telegram_id"]

        profile_data = {"name": "John", "age": 25, "gender": "male", "city": "Moscow"}
        await async_client.post(
            "/api/v1/profiles/create",
            json=profile_data,
            headers={"X-Telegram-Id": str(telegram_id)},
        )

        # Act - update profile
        update_data = {"name": "John Updated", "age": 26}
        response = await async_client.patch(
            "/api/v1/profiles/update",
            json=update_data,
            headers={"X-Telegram-Id": str(telegram_id)},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "John Updated"
        assert data["age"] == 26

    @pytest.mark.asyncio
    async def test_update_search_mode(self, async_client: AsyncClient):
        """Test updating search mode."""
        # Arrange - register and create profile
        user = await self._register_user(async_client, 555555)
        telegram_id = user["telegram_id"]

        profile_data = {"name": "John", "age": 25, "gender": "male", "city": "Moscow"}
        await async_client.post(
            "/api/v1/profiles/create",
            json=profile_data,
            headers={"X-Telegram-Id": str(telegram_id)},
        )

        # Act - update search mode
        response = await async_client.patch(
            "/api/v1/profiles/search-mode",
            json={"search_city_mode": "global"},
            headers={"X-Telegram-Id": str(telegram_id)},
        )

        # Assert
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_feed_success(self, async_client: AsyncClient):
        """Test getting user feed."""
        # Arrange - register, create profile for current user, and create other profiles
        user1 = await self._register_user(async_client, 666666)
        user1_telegram_id = user1["telegram_id"]

        # Create current user's profile
        profile_data = {"name": "User1", "age": 25, "gender": "male", "city": "Moscow"}
        await async_client.post(
            "/api/v1/profiles/create",
            json=profile_data,
            headers={"X-Telegram-Id": str(user1_telegram_id)},
        )

        # Create other profiles
        for i in range(3):
            user = await self._register_user(async_client, 700000 + i)
            other_profile = {
                "name": f"User{i}",
                "age": 25 + i,
                "gender": "female",
                "city": "Moscow",
            }
            await async_client.post(
                "/api/v1/profiles/create",
                json=other_profile,
                headers={"X-Telegram-Id": str(user["telegram_id"])},
            )

        # Act - get feed
        response = await async_client.get(
            "/api/v1/profiles/feed", headers={"X-Telegram-Id": str(user1_telegram_id)}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_get_feed_profile_not_created(self, async_client: AsyncClient):
        """Test getting feed when user has no profile."""
        # Arrange - register user but don't create profile
        user = await self._register_user(async_client, 888888)
        telegram_id = user["telegram_id"]

        # Act
        response = await async_client.get(
            "/api/v1/profiles/feed", headers={"X-Telegram-Id": str(telegram_id)}
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_one_active_profile_per_user(self, async_client: AsyncClient):
        """Test that user cannot create second active profile."""
        # Arrange - register user and create profile
        user = await self._register_user(async_client, 999999)
        telegram_id = user["telegram_id"]

        profile_data = {"name": "John", "age": 25, "gender": "male", "city": "Moscow"}
        await async_client.post(
            "/api/v1/profiles/create",
            json=profile_data,
            headers={"X-Telegram-Id": str(telegram_id)},
        )

        # Act - try to create second profile
        profile_data2 = {"name": "Jane", "age": 28, "gender": "female", "city": "SPB"}
        response = await async_client.post(
            "/api/v1/profiles/create",
            json=profile_data2,
            headers={"X-Telegram-Id": str(telegram_id)},
        )

        # Assert
        assert response.status_code == 409  # Conflict
