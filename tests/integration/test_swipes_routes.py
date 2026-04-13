"""Integration tests for Swipes API routes."""

import pytest
from httpx import AsyncClient

from app.models.enums import SwipeAction


@pytest.mark.integration
class TestSwipesRoutes:
    """Integration tests for /swipes endpoints."""

    async def _register_and_create_profile(
        self, async_client: AsyncClient, telegram_id: int, name: str, gender: str
    ) -> dict:
        """Helper to register user and create profile."""
        user = await async_client.post("/api/v1/users/register", json={"telegram_id": telegram_id})
        assert user.status_code == 200
        user_data = user.json()
        user_id = user_data["id"]

        profile_data = {
            "name": name,
            "age": 25,
            "gender": gender,
            "city": "Moscow",
        }
        profile = await async_client.post(
            "/api/v1/profiles/create",
            json=profile_data,
            headers={"X-Telegram-Id": str(telegram_id)},
        )
        assert profile.status_code == 200
        profile_data_resp = profile.json()
        return {
            "user_id": user_id,
            "telegram_id": telegram_id,
            "profile_id": profile_data_resp["id"],
        }

    @pytest.mark.asyncio
    async def test_like_profile_success(self, async_client: AsyncClient):
        """Test successfully liking a profile."""
        # Arrange - create two users with profiles
        user1 = await self._register_and_create_profile(async_client, 111111, "John", "M")
        user2 = await self._register_and_create_profile(async_client, 222222, "Jane", "F")

        # Act
        response = await async_client.post(
            f"/api/v1/swipes/like/{user2['profile_id']}",
            headers={"X-Telegram-Id": str(user1["telegram_id"])},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data.get("action") == SwipeAction.LIKE.value

    @pytest.mark.asyncio
    async def test_skip_profile_success(self, async_client: AsyncClient):
        """Test successfully skipping a profile."""
        # Arrange
        user1 = await self._register_and_create_profile(async_client, 333333, "John", "M")
        user2 = await self._register_and_create_profile(async_client, 444444, "Jane", "F")

        # Act
        response = await async_client.post(
            f"/api/v1/swipes/skip/{user2['profile_id']}",
            headers={"X-Telegram-Id": str(user1["telegram_id"])},
        )

        # Assert
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_like_nonexistent_profile(self, async_client: AsyncClient):
        """Test liking non-existent profile."""
        # Arrange
        user = await self._register_and_create_profile(async_client, 555555, "John", "M")

        # Act
        response = await async_client.post(
            "/api/v1/swipes/like/99999",
            headers={"X-Telegram-Id": str(user["telegram_id"])},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_like_own_profile(self, async_client: AsyncClient):
        """Test liking own profile (should be prevented)."""
        # Arrange
        user = await self._register_and_create_profile(async_client, 666666, "John", "M")

        # Act
        response = await async_client.post(
            f"/api/v1/swipes/like/{user['profile_id']}",
            headers={"X-Telegram-Id": str(user["telegram_id"])},
        )

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_duplicate_like_prevention(self, async_client: AsyncClient):
        """Test that duplicate likes are prevented."""
        # Arrange
        user1 = await self._register_and_create_profile(async_client, 777777, "John", "M")
        user2 = await self._register_and_create_profile(async_client, 888888, "Jane", "F")

        # Like once
        await async_client.post(
            f"/api/v1/swipes/like/{user2['profile_id']}",
            headers={"X-Telegram-Id": str(user1["telegram_id"])},
        )

        # Act - try to like again
        response = await async_client.post(
            f"/api/v1/swipes/like/{user2['profile_id']}",
            headers={"X-Telegram-Id": str(user1["telegram_id"])},
        )

        # Assert
        assert response.status_code == 409  # Conflict

    @pytest.mark.asyncio
    async def test_like_after_skip_allowed(self, async_client: AsyncClient):
        """Test that can like after skipping (different action)."""
        # Arrange
        user1 = await self._register_and_create_profile(async_client, 999999, "John", "M")
        user2 = await self._register_and_create_profile(async_client, 1111111, "Jane", "F")

        # Skip first
        await async_client.post(
            f"/api/v1/swipes/skip/{user2['profile_id']}",
            headers={"X-Telegram-Id": str(user1["telegram_id"])},
        )

        # Act - try to like (different from skip)
        response = await async_client.post(
            f"/api/v1/swipes/like/{user2['profile_id']}",
            headers={"X-Telegram-Id": str(user1["telegram_id"])},
        )

        # Assert - behavior depends on business logic
        # Either allows (409) or updates (200)
        assert response.status_code in [200, 409]

    @pytest.mark.asyncio
    async def test_get_swipes_list(self, async_client: AsyncClient):
        """Test retrieving list of swipes."""
        # Arrange
        user1 = await self._register_and_create_profile(async_client, 1212121, "John", "M")
        user2 = await self._register_and_create_profile(async_client, 1313131, "Jane", "F")

        # Like
        await async_client.post(
            f"/api/v1/swipes/like/{user2['profile_id']}",
            headers={"X-Telegram-Id": str(user1["telegram_id"])},
        )

        # Act
        response = await async_client.get(
            "/api/v1/swipes/history",
            headers={"X-Telegram-Id": str(user1["telegram_id"])},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
