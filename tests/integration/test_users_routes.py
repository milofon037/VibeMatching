"""Integration tests for Users API routes."""

import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.integration
class TestUsersRoutes:
    """Integration tests for /users endpoints."""

    @pytest.mark.asyncio
    async def test_register_user_success(self, async_client: AsyncClient, test_db):
        """Test successful user registration via POST /users/register."""
        # Arrange
        payload = {"telegram_id": 123456789}

        # Act
        response = await async_client.post("/api/v1/users/register", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["telegram_id"] == 123456789
        assert "id" in data
        assert "created_at" in data

        # Verify in database
        from sqlalchemy import select

        result = await test_db.execute(select(User).where(User.telegram_id == 123456789))
        user_in_db = result.scalar_one_or_none()
        assert user_in_db is not None
        assert user_in_db.telegram_id == 123456789

    @pytest.mark.asyncio
    async def test_register_user_idempotent(self, async_client: AsyncClient):
        """Test that user registration is idempotent."""
        # Arrange
        payload = {"telegram_id": 999}

        # Act - register twice
        response1 = await async_client.post("/api/v1/users/register", json=payload)
        response2 = await async_client.post("/api/v1/users/register", json=payload)

        # Assert - both should succeed with same user
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json()["id"] == response2.json()["id"]

    @pytest.mark.asyncio
    async def test_register_user_with_referral_code(self, async_client: AsyncClient, test_db):
        """Test user registration with referral code."""
        # Arrange
        payload = {"telegram_id": 111111, "referral_code": "REF_CODE_123"}

        # Act
        response = await async_client.post("/api/v1/users/register", json=payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["telegram_id"] == 111111
        assert data.get("referral_code") == "REF_CODE_123"

    @pytest.mark.asyncio
    async def test_register_user_invalid_payload(self, async_client: AsyncClient):
        """Test registration with invalid payload."""
        # Arrange - missing required telegram_id
        payload = {}

        # Act
        response = await async_client.post("/api/v1/users/register", json=payload)

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, async_client: AsyncClient, test_db):
        """Test getting current user info."""
        # Arrange - register user first
        create_response = await async_client.post("/api/v1/users/register", json={"telegram_id": 222})
        user_data = create_response.json()

        # Act - get current user (need to pass auth with telegram_id)
        response = await async_client.get("/api/v1/users/me", headers={"X-Telegram-Id": "222"})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_data["id"]
        assert data["telegram_id"] == 222

    @pytest.mark.asyncio
    async def test_get_current_user_not_found(self, async_client: AsyncClient):
        """Test getting non-existent user."""
        # Act - try to get user that doesn't exist
        response = await async_client.get("/api/v1/users/me", headers={"X-Telegram-Id": "9999"})

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_activity_success(self, async_client: AsyncClient):
        """Test updating user activity."""
        # Arrange - register user first
        create_response = await async_client.post("/api/v1/users/register", json={"telegram_id": 333})
        user_data = create_response.json()

        # Act - update activity with telegram_id
        response = await async_client.patch("/api/v1/users/activity", headers={"X-Telegram-Id": "333"})

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == user_data["id"]
        assert "last_active_at" in data

    @pytest.mark.asyncio
    async def test_update_activity_user_not_found(self, async_client: AsyncClient):
        """Test updating activity for non-existent user."""
        # Act
        response = await async_client.patch("/api/v1/users/activity", headers={"X-Telegram-Id": "99999"})

        # Assert
        assert response.status_code == 404
