"""Integration tests for Photos API routes."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestPhotosRoutes:
    """Integration tests for /photos endpoints."""

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

    @pytest.mark.asyncio
    async def test_upload_photo_success(self, async_client: AsyncClient):
        """Test successful photo upload."""
        # Arrange
        user = await self._register_and_create_profile(async_client, 111111, "John", "M")

        # Create a small test image
        # For integration test, we'll use a simple PNG header as bytes
        image_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00"
            b"\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx"
            b"\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x055\xfb\xf3\x84\x00\x00\x00\x00IEND\xaeB`\x82"
        )

        # Act
        response = await async_client.post(
            "/api/v1/photos/upload",
            files={"file": ("test.png", image_bytes, "image/png")},
            headers={
                "X-Telegram-Id": str(user["telegram_id"]),
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data.get("photo", {}).get("id")

    @pytest.mark.asyncio
    async def test_upload_photo_invalid_content_type(self, async_client: AsyncClient):
        """Test uploading with invalid content type."""
        # Arrange
        user = await self._register_and_create_profile(async_client, 222222, "John", "M")

        # Act
        response = await async_client.post(
            "/api/v1/photos/upload",
            files={"file": ("test.txt", b"invalid data", "text/plain")},
            headers={
                "X-Telegram-Id": str(user["telegram_id"]),
            },
        )

        # Assert
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_user_photos_success(self, async_client: AsyncClient):
        """Test retrieving user's photos."""
        # Arrange
        user = await self._register_and_create_profile(async_client, 333333, "John", "M")

        # Upload a photo
        image_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00"
            b"\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx"
            b"\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x055\xfb\xf3\x84\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        await async_client.post(
            "/api/v1/photos/upload",
            files={"file": ("test.png", image_bytes, "image/png")},
            headers={
                "X-Telegram-Id": str(user["telegram_id"]),
            },
        )

        # Act
        response = await async_client.get(
            "/api/v1/photos/my",
            headers={"X-Telegram-Id": str(user["telegram_id"])},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_user_photos_empty(self, async_client: AsyncClient):
        """Test retrieving photos when user has none."""
        # Arrange
        user = await self._register_and_create_profile(async_client, 444444, "John", "M")

        # Act
        response = await async_client.get(
            "/api/v1/photos/my",
            headers={"X-Telegram-Id": str(user["telegram_id"])},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_delete_photo_success(self, async_client: AsyncClient):
        """Test deleting a photo."""
        # Arrange
        user = await self._register_and_create_profile(async_client, 555555, "John", "M")

        # Upload a photo
        image_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00"
            b"\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx"
            b"\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x055\xfb\xf3\x84\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        upload_response = await async_client.post(
            "/api/v1/photos/upload",
            files={"file": ("test.png", image_bytes, "image/png")},
            headers={
                "X-Telegram-Id": str(user["telegram_id"]),
            },
        )
        photo_data = upload_response.json()
        photo_id = photo_data["photo"]["id"]

        # Act
        response = await async_client.delete(
            f"/api/v1/photos/{photo_id}",
            headers={"X-Telegram-Id": str(user["telegram_id"])},
        )

        # Assert
        assert response.status_code == 204 or response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_nonexistent_photo(self, async_client: AsyncClient):
        """Test deleting non-existent photo."""
        # Arrange
        user = await self._register_and_create_profile(async_client, 666666, "John", "M")

        # Act
        response = await async_client.delete(
            "/api/v1/photos/99999",
            headers={"X-Telegram-Id": str(user["telegram_id"])},
        )

        # Assert
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_set_main_photo(self, async_client: AsyncClient):
        """Test setting a photo as main."""
        # Arrange
        user = await self._register_and_create_profile(async_client, 777777, "John", "M")

        # Upload a photo
        image_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00"
            b"\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx"
            b"\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x055\xfb\xf3\x84\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        upload_response = await async_client.post(
            "/api/v1/photos/upload",
            files={"file": ("test.png", image_bytes, "image/png")},
            headers={
                "X-Telegram-Id": str(user["telegram_id"]),
            },
        )
        photo_data = upload_response.json()
        photo_id = photo_data["photo"]["id"]

        # Act
        response = await async_client.post(
            f"/api/v1/photos/{photo_id}/set-main",
            headers={"X-Telegram-Id": str(user["telegram_id"])},
        )

        # Assert
        assert response.status_code == 200 or response.status_code == 204
