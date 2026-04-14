"""Unit tests for base rank score formula."""

from datetime import UTC, datetime, timedelta

import pytest

from app.services.rating_score import calculate_base_rank


@pytest.mark.unit
def test_calculate_base_rank_max_score() -> None:
    """Returns 1.0 when all normalized components are maximal."""
    last_active_at = datetime.now(tz=UTC)

    result = calculate_base_rank(
        photo_count=5,
        bio="x" * 500,
        last_active_at=last_active_at,
    )

    assert result == pytest.approx(1.0)


@pytest.mark.unit
def test_calculate_base_rank_returns_zero_for_empty_and_inactive_profile() -> None:
    """Returns 0.0 when all three input signals are at minimum."""
    last_active_at = datetime.now(tz=UTC) - timedelta(days=45)

    result = calculate_base_rank(
        photo_count=0,
        bio="",
        last_active_at=last_active_at,
    )

    assert result == pytest.approx(0.0)


@pytest.mark.unit
def test_calculate_base_rank_uses_weighted_components() -> None:
    """Uses 0.2/0.2/0.6 weights for photo, bio and activity signals."""
    # photo_count=3 => 0.6, bio_len=250 => 0.5, activity=15 days => 0.5.
    # expected = 0.6*0.2 + 0.5*0.2 + 0.5*0.6 = 0.52
    last_active_at = datetime.now(tz=UTC) - timedelta(days=15)

    result = calculate_base_rank(
        photo_count=3,
        bio="x" * 250,
        last_active_at=last_active_at,
    )

    assert result == pytest.approx(0.52)


@pytest.mark.unit
def test_calculate_base_rank_handles_naive_datetime_as_utc() -> None:
    """Treats naive last_active_at as UTC and keeps score in [0..1]."""
    naive_last_active = datetime.now(tz=UTC).replace(tzinfo=None) - timedelta(days=1)

    result = calculate_base_rank(
        photo_count=1,
        bio="bio",
        last_active_at=naive_last_active,
    )

    assert 0.0 <= result <= 1.0
