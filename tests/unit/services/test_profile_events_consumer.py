import pytest

from ranking_service.consumers.profile_events_consumer import ProfileEventsConsumer
from ranking_service.repositories.profiles_index import InMemoryProfilesIndexRepository


@pytest.mark.unit
@pytest.mark.asyncio
async def test_consumer_updates_interests_document() -> None:
    index = InMemoryProfilesIndexRepository()
    consumer = ProfileEventsConsumer(index_repository=index)

    processed = await consumer.process(
        {
            "event_id": "evt-1",
            "event_type": "interests_updated",
            "dedup_key": "interests_updated:10:1,2",
            "payload": {"profile_id": 10, "interest_ids": [1, 2]},
        }
    )

    assert processed is True
    assert index.documents[10]["interests"] == [1, 2]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_consumer_skips_duplicate_event_by_dedup_key() -> None:
    index = InMemoryProfilesIndexRepository()
    consumer = ProfileEventsConsumer(index_repository=index)

    first = {
        "event_id": "evt-1",
        "event_type": "rating_updated",
        "dedup_key": "rating_updated:10:0.800000",
        "payload": {"profile_id": 10, "base_rank": 0.8, "user_id": 5},
    }
    duplicate = {
        "event_id": "evt-2",
        "event_type": "rating_updated",
        "dedup_key": "rating_updated:10:0.800000",
        "payload": {"profile_id": 10, "base_rank": 0.8, "user_id": 5},
    }

    first_processed = await consumer.process(first)
    second_processed = await consumer.process(duplicate)

    assert first_processed is True
    assert second_processed is False
    assert index.documents[10]["base_rank"] == 0.8


@pytest.mark.unit
@pytest.mark.asyncio
async def test_consumer_updates_base_rank_document() -> None:
    index = InMemoryProfilesIndexRepository()
    consumer = ProfileEventsConsumer(index_repository=index)

    processed = await consumer.process(
        {
            "event_id": "evt-rating-1",
            "event_type": "rating_updated",
            "dedup_key": "rating_updated:99:0.550000",
            "payload": {"profile_id": 99, "base_rank": 0.55, "user_id": 20},
        }
    )

    assert processed is True
    assert index.documents[99]["base_rank"] == pytest.approx(0.55)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_consumer_initializes_index_once() -> None:
    class SpyIndexRepository(InMemoryProfilesIndexRepository):
        def __init__(self) -> None:
            super().__init__()
            self.ensure_calls = 0

        async def ensure_index(self) -> None:
            self.ensure_calls += 1

    index = SpyIndexRepository()
    consumer = ProfileEventsConsumer(index_repository=index)

    await consumer.process(
        {
            "event_id": "evt-1",
            "event_type": "interests_updated",
            "dedup_key": "interests_updated:10:1",
            "payload": {"profile_id": 10, "interest_ids": [1]},
        }
    )
    await consumer.process(
        {
            "event_id": "evt-2",
            "event_type": "rating_updated",
            "dedup_key": "rating_updated:10:0.200000",
            "payload": {"profile_id": 10, "base_rank": 0.2, "user_id": 1},
        }
    )

    assert index.ensure_calls == 1
