"""Unit tests for RatingsRepository history recording."""

import pytest
from sqlalchemy import select

from app.models.rating_history import RatingHistory
from app.models.user import User
from app.repositories.ratings_repository import RatingsRepository


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upsert_base_rank_creates_history_on_first_insert(test_db):
    user = User(telegram_id=1001)
    test_db.add(user)
    await test_db.flush()

    repository = RatingsRepository(session=test_db)

    rating = await repository.upsert_base_rank(user_id=user.id, base_rank=0.5)
    await test_db.commit()

    assert rating.base_rank == pytest.approx(0.5)

    result = await test_db.execute(
        select(RatingHistory).where(RatingHistory.user_id == user.id)
    )
    history_rows = result.scalars().all()

    assert len(history_rows) == 1
    assert history_rows[0].event_type == "base_rank_initialized"
    assert history_rows[0].delta == 500


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upsert_base_rank_creates_history_on_recalculation(test_db):
    user = User(telegram_id=1002)
    test_db.add(user)
    await test_db.flush()

    repository = RatingsRepository(session=test_db)

    await repository.upsert_base_rank(user_id=user.id, base_rank=0.5)
    await repository.upsert_base_rank(user_id=user.id, base_rank=0.9)
    await test_db.commit()

    result = await test_db.execute(
        select(RatingHistory)
        .where(RatingHistory.user_id == user.id)
        .order_by(RatingHistory.id.asc())
    )
    history_rows = result.scalars().all()

    assert len(history_rows) == 2
    assert history_rows[0].event_type == "base_rank_initialized"
    assert history_rows[0].delta == 500
    assert history_rows[1].event_type == "base_rank_recalculated"
    assert history_rows[1].delta == 400


@pytest.mark.unit
@pytest.mark.asyncio
async def test_upsert_base_rank_does_not_create_history_for_same_value(test_db):
    user = User(telegram_id=1003)
    test_db.add(user)
    await test_db.flush()

    repository = RatingsRepository(session=test_db)

    await repository.upsert_base_rank(user_id=user.id, base_rank=0.75)
    await repository.upsert_base_rank(user_id=user.id, base_rank=0.75)
    await test_db.commit()

    result = await test_db.execute(
        select(RatingHistory)
        .where(RatingHistory.user_id == user.id)
        .order_by(RatingHistory.id.asc())
    )
    history_rows = result.scalars().all()

    assert len(history_rows) == 1
    assert history_rows[0].event_type == "base_rank_initialized"
