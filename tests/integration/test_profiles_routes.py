"""Integration tests for Profiles API routes."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.config import settings
from app.models.interest import Interest
from app.models.rating import Rating
from app.models.user import User
from app.services.ranking_client import RankingServiceClient
from ranking_service.domain.schemas import RankCandidate
from ranking_service.services.scoring import rank_candidates


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

    async def _create_profile(
        self,
        async_client: AsyncClient,
        telegram_id: int,
        *,
        name: str,
        gender: str,
        age: int = 25,
        city: str = "Moscow",
    ) -> dict:
        response = await async_client.post(
            "/api/v1/profiles/create",
            json={"name": name, "age": age, "gender": gender, "city": city},
            headers={"X-Telegram-Id": str(telegram_id)},
        )
        assert response.status_code == 200
        return response.json()

    async def _set_base_rank(self, test_db, telegram_id: int, base_rank: float) -> None:
        result = await test_db.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one()

        rating_result = await test_db.execute(select(Rating).where(Rating.user_id == user.id))
        rating = rating_result.scalar_one_or_none()
        if rating is None:
            test_db.add(Rating(user_id=user.id, base_rank=base_rank))
        else:
            rating.base_rank = base_rank
        await test_db.commit()

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

    @pytest.mark.asyncio
    async def test_feed_order_changes_after_interests_update(
        self, async_client: AsyncClient, test_db, monkeypatch
    ):
        """Interest updates should affect ranking order in feed."""

        async def fake_rank_feed(
            self,
            user_id: int,
            user_interest_ids: list[int],
            excluded_ids: list[int],
            candidates,
            limit: int,
        ) -> list[int]:
            rank_candidates_payload = [
                RankCandidate(
                    profile_id=item.profile_id,
                    base_rank=item.base_rank,
                    interests=item.interests,
                )
                for item in candidates
            ]
            return rank_candidates(
                user_id=user_id,
                user_interest_ids=user_interest_ids,
                candidates=rank_candidates_payload,
                excluded_ids=excluded_ids,
                limit=limit,
            )

        monkeypatch.setattr(settings, "ranking_service_enabled", True)
        monkeypatch.setattr(RankingServiceClient, "rank_feed", fake_rank_feed)

        test_db.add_all([Interest(name="music"), Interest(name="books")])
        await test_db.commit()

        interests_response = await async_client.get("/api/v1/interests")
        assert interests_response.status_code == 200
        interests_by_name = {item["name"]: item["id"] for item in interests_response.json()}

        me = await self._register_user(async_client, 901001)
        candidate_match = await self._register_user(async_client, 901002)
        candidate_other = await self._register_user(async_client, 901003)

        await self._create_profile(
            async_client,
            me["telegram_id"],
            name="Me",
            gender="male",
        )
        profile_match = await self._create_profile(
            async_client,
            candidate_match["telegram_id"],
            name="MatchByInterest",
            gender="female",
        )
        profile_other = await self._create_profile(
            async_client,
            candidate_other["telegram_id"],
            name="OtherInterest",
            gender="female",
        )

        for tg_id in [me["telegram_id"], candidate_match["telegram_id"], candidate_other["telegram_id"]]:
            await self._set_base_rank(test_db, tg_id, 0.5)

        response = await async_client.patch(
            "/api/v1/profiles/interests",
            json={"interest_ids": [interests_by_name["music"]]},
            headers={"X-Telegram-Id": str(me["telegram_id"])},
        )
        assert response.status_code == 200

        response = await async_client.patch(
            "/api/v1/profiles/interests",
            json={"interest_ids": [interests_by_name["music"]]},
            headers={"X-Telegram-Id": str(candidate_match["telegram_id"])},
        )
        assert response.status_code == 200

        response = await async_client.patch(
            "/api/v1/profiles/interests",
            json={"interest_ids": [interests_by_name["books"]]},
            headers={"X-Telegram-Id": str(candidate_other["telegram_id"])},
        )
        assert response.status_code == 200

        feed_response = await async_client.get(
            "/api/v1/profiles/feed",
            headers={"X-Telegram-Id": str(me["telegram_id"])},
        )
        assert feed_response.status_code == 200
        feed = feed_response.json()

        assert feed[0]["id"] == profile_match["id"]
        assert feed[1]["id"] == profile_other["id"]

    @pytest.mark.asyncio
    async def test_feed_order_changes_after_base_rank_update(
        self, async_client: AsyncClient, test_db, monkeypatch
    ):
        """Base rank updates should affect ranking order in feed."""

        async def fake_rank_feed(
            self,
            user_id: int,
            user_interest_ids: list[int],
            excluded_ids: list[int],
            candidates,
            limit: int,
        ) -> list[int]:
            rank_candidates_payload = [
                RankCandidate(
                    profile_id=item.profile_id,
                    base_rank=item.base_rank,
                    interests=item.interests,
                )
                for item in candidates
            ]
            return rank_candidates(
                user_id=user_id,
                user_interest_ids=user_interest_ids,
                candidates=rank_candidates_payload,
                excluded_ids=excluded_ids,
                limit=limit,
            )

        monkeypatch.setattr(settings, "ranking_service_enabled", True)
        monkeypatch.setattr(RankingServiceClient, "rank_feed", fake_rank_feed)

        me = await self._register_user(async_client, 902001)
        candidate_high = await self._register_user(async_client, 902002)
        candidate_low = await self._register_user(async_client, 902003)

        await self._create_profile(async_client, me["telegram_id"], name="Me", gender="male")
        profile_high = await self._create_profile(
            async_client,
            candidate_high["telegram_id"],
            name="HighRank",
            gender="female",
        )
        profile_low = await self._create_profile(
            async_client,
            candidate_low["telegram_id"],
            name="LowRank",
            gender="female",
        )

        await self._set_base_rank(test_db, candidate_high["telegram_id"], 0.9)
        await self._set_base_rank(test_db, candidate_low["telegram_id"], 0.2)

        feed_response = await async_client.get(
            "/api/v1/profiles/feed",
            headers={"X-Telegram-Id": str(me["telegram_id"])},
        )
        assert feed_response.status_code == 200
        feed = feed_response.json()

        assert feed[0]["id"] == profile_high["id"]
        assert feed[1]["id"] == profile_low["id"]

    @pytest.mark.asyncio
    async def test_stage1_e2e_smoke_registration_profile_interests_feed(
        self, async_client: AsyncClient, test_db, monkeypatch
    ):
        """E2E smoke: register -> profile -> interests -> feed."""

        async def fake_rank_feed(
            self,
            user_id: int,
            user_interest_ids: list[int],
            excluded_ids: list[int],
            candidates,
            limit: int,
        ) -> list[int]:
            rank_candidates_payload = [
                RankCandidate(
                    profile_id=item.profile_id,
                    base_rank=item.base_rank,
                    interests=item.interests,
                )
                for item in candidates
            ]
            return rank_candidates(
                user_id=user_id,
                user_interest_ids=user_interest_ids,
                candidates=rank_candidates_payload,
                excluded_ids=excluded_ids,
                limit=limit,
            )

        monkeypatch.setattr(settings, "ranking_service_enabled", True)
        monkeypatch.setattr(RankingServiceClient, "rank_feed", fake_rank_feed)

        test_db.add(Interest(name="travel"))
        await test_db.commit()

        interests_response = await async_client.get("/api/v1/interests")
        assert interests_response.status_code == 200
        travel_interest_id = next(
            item["id"] for item in interests_response.json() if item["name"] == "travel"
        )

        requester = await self._register_user(async_client, 903001)
        candidate = await self._register_user(async_client, 903002)

        await self._create_profile(async_client, requester["telegram_id"], name="Requester", gender="male")
        candidate_profile = await self._create_profile(
            async_client,
            candidate["telegram_id"],
            name="Candidate",
            gender="female",
        )

        response = await async_client.patch(
            "/api/v1/profiles/interests",
            json={"interest_ids": [travel_interest_id]},
            headers={"X-Telegram-Id": str(requester["telegram_id"])},
        )
        assert response.status_code == 200

        response = await async_client.patch(
            "/api/v1/profiles/interests",
            json={"interest_ids": [travel_interest_id]},
            headers={"X-Telegram-Id": str(candidate["telegram_id"])},
        )
        assert response.status_code == 200

        await self._set_base_rank(test_db, requester["telegram_id"], 0.5)
        await self._set_base_rank(test_db, candidate["telegram_id"], 0.7)

        feed_response = await async_client.get(
            "/api/v1/profiles/feed",
            headers={"X-Telegram-Id": str(requester["telegram_id"])},
        )
        assert feed_response.status_code == 200
        feed = feed_response.json()

        assert len(feed) >= 1
        assert feed[0]["id"] == candidate_profile["id"]
