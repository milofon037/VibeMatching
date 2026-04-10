"""Integration tests for Matches API routes."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestMatchesRoutes:
    """Integration tests for /matches endpoints."""

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
        return {"user_id": user_id, "telegram_id": telegram_id, "profile_id": profile_data_resp["id"]}

    async def _create_mutual_like(
        self,
        async_client: AsyncClient,
        user1_telegram_id: int,
        user1_profile_id: int,
        user2_telegram_id: int,
        user2_profile_id: int,
    ):
        """Helper to create mutual likes between two users."""
        # User1 likes User2
        await async_client.post(
            f"/api/v1/swipes/like/{user2_profile_id}",
            headers={"X-Telegram-Id": str(user1_telegram_id)},
        )

        # User2 likes User1
        await async_client.post(
            f"/api/v1/swipes/like/{user1_profile_id}",
            headers={"X-Telegram-Id": str(user2_telegram_id)},
        )

    @pytest.mark.asyncio
    async def test_list_matches_success(self, async_client: AsyncClient):
        """Test retrieving list of matches."""
        # Arrange - create mutual likes
        user1 = await self._register_and_create_profile(async_client, 111111, "John", "M")
        user2 = await self._register_and_create_profile(async_client, 222222, "Jane", "F")

        await self._create_mutual_like(
            async_client,
            user1["telegram_id"],
            user1["profile_id"],
            user2["telegram_id"],
            user2["profile_id"],
        )

        # Act
        response = await async_client.get(
            "/api/v1/matches/list",
            headers={"X-Telegram-Id": str(user1["telegram_id"])},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_list_matches_empty(self, async_client: AsyncClient):
        """Test getting matches when user has no matches."""
        # Arrange
        user = await self._register_and_create_profile(async_client, 333333, "John", "M")

        # Act
        response = await async_client.get(
            "/api/v1/matches/list",
            headers={"X-Telegram-Id": str(user["telegram_id"])},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_start_dialog_success(self, async_client: AsyncClient):
        """Test starting dialog with matched user."""
        # Arrange - create mutual likes
        user1 = await self._register_and_create_profile(async_client, 444444, "John", "M")
        user2 = await self._register_and_create_profile(async_client, 555555, "Jane", "F")

        await self._create_mutual_like(
            async_client,
            user1["telegram_id"],
            user1["profile_id"],
            user2["telegram_id"],
            user2["profile_id"],
        )

        list_response = await async_client.get(
            "/api/v1/matches/list",
            headers={"X-Telegram-Id": str(user1["telegram_id"])},
        )
        assert list_response.status_code == 200
        match_id = list_response.json()[0]["id"]

        # Act
        response = await async_client.post(
            f"/api/v1/matches/start-dialog/{match_id}",
            headers={"X-Telegram-Id": str(user1["telegram_id"])},
        )

        # Assert
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_start_dialog_without_match(self, async_client: AsyncClient):
        """Test starting dialog with non-matched user (should fail)."""
        # Arrange
        user1 = await self._register_and_create_profile(async_client, 666666, "John", "M")
        user2 = await self._register_and_create_profile(async_client, 777777, "Jane", "F")

        # Act - no mutual likes
        response = await async_client.post(
            f"/api/v1/matches/start-dialog/{user2['user_id']}",
            headers={"X-Telegram-Id": str(user1["telegram_id"])},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_match_details(self, async_client: AsyncClient):
        """Test getting details of a specific match."""
        # Arrange - create mutual likes
        user1 = await self._register_and_create_profile(async_client, 888888, "John", "M")
        user2 = await self._register_and_create_profile(async_client, 999999, "Jane", "F")

        await self._create_mutual_like(
            async_client,
            user1["telegram_id"],
            user1["profile_id"],
            user2["telegram_id"],
            user2["profile_id"],
        )

        # Act
        response = await async_client.get(
            "/api/v1/matches/list",
            headers={"X-Telegram-Id": str(user1["telegram_id"])},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert any(
            (item.get("user1_id") == user2["user_id"]) or (item.get("user2_id") == user2["user_id"])
            for item in data
        )

    @pytest.mark.asyncio
    async def test_multiple_matches(self, async_client: AsyncClient):
        """Test user with multiple matches."""
        # Arrange
        user1 = await self._register_and_create_profile(async_client, 1111111, "John", "M")

        # Create multiple matches
        for i in range(3):
            user = await self._register_and_create_profile(async_client, 1111111 + i + 1, f"Jane{i}", "F")
            await self._create_mutual_like(
                async_client,
                user1["telegram_id"],
                user1["profile_id"],
                user["telegram_id"],
                user["profile_id"],
            )

        # Act
        response = await async_client.get(
            "/api/v1/matches/list",
            headers={"X-Telegram-Id": str(user1["telegram_id"])},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
