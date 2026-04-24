"""Unit tests for base rank score formula."""

from datetime import UTC, datetime, timedelta

import pytest

from app.services.rating_score import calculate_base_rank


@pytest.mark.unit
def test_calculate_base_rank_max_score() -> None:
    """Returns 1.0 when all normalized components are maximal and no referral bonus."""
    last_active_at = datetime.now(tz=UTC)

    result = calculate_base_rank(
        photo_count=5,
        bio="x" * 500,
        last_active_at=last_active_at,
    )

    assert result == pytest.approx(1.0)


@pytest.mark.unit
def test_calculate_base_rank_adds_referral_bonus() -> None:
    """Adds referral bonus on top of the weighted base components."""
    last_active_at = datetime.now(tz=UTC)

    result = calculate_base_rank(
        photo_count=5,
        bio="x" * 500,
        last_active_at=last_active_at,
        referred_users_count=2,
    )

    assert result == pytest.approx(1.1)


@pytest.mark.unit
def test_calculate_base_rank_adds_behavioral_component() -> None:
    """Adds weekly behavioral component from likes/ratio/matches."""
    last_active_at = datetime.now(tz=UTC)

    result = calculate_base_rank(
        photo_count=0,
        bio="",
        last_active_at=last_active_at,
        likes_received_count=20,
        skips_received_count=0,
        matches_count=20,
    )

    # 0.6 from activity + behavioral 1.0 * 0.2.
    assert result == pytest.approx(0.8)


@pytest.mark.unit
def test_calculate_base_rank_caps_referral_bonus() -> None:
    """Caps referral bonus to avoid unbounded score growth."""
    last_active_at = datetime.now(tz=UTC)

    result = calculate_base_rank(
        photo_count=0,
        bio="",
        last_active_at=last_active_at,
        referred_users_count=999,
    )

    # 0.6 from activity + capped 0.5 bonus.
    assert result == pytest.approx(1.1)


@pytest.mark.unit
def test_calculate_base_rank_caps_total_score_with_behavior_and_referrals() -> None:
    """Caps total score even when all components are maximal."""
    last_active_at = datetime.now(tz=UTC)

    result = calculate_base_rank(
        photo_count=5,
        bio="x" * 500,
        last_active_at=last_active_at,
        referred_users_count=999,
        likes_received_count=999,
        skips_received_count=0,
        matches_count=999,
    )

    assert result == pytest.approx(1.7)


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
    """Treats naive last_active_at as UTC and keeps score in valid range."""
    naive_last_active = datetime.now(tz=UTC).replace(tzinfo=None) - timedelta(days=1)

    result = calculate_base_rank(
        photo_count=1,
        bio="bio",
        last_active_at=naive_last_active,
    )

    assert 0.0 <= result <= 1.7
