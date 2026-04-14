"""Unit tests for ranking service scoring logic."""

import pytest

from ranking_service.domain.schemas import RankCandidate
from ranking_service.services.scoring import rank_candidates


@pytest.mark.unit
def test_rank_candidates_prioritizes_interest_match() -> None:
    """Interest overlap should strongly affect stage-1 score."""
    candidates = [
        RankCandidate(profile_id=10, base_rank=0.8, interests=[2]),
        RankCandidate(profile_id=20, base_rank=0.6, interests=[1]),
    ]

    result = rank_candidates(
        user_id=1,
        user_interest_ids=[1],
        candidates=candidates,
        excluded_ids=[],
        limit=10,
    )

    assert result[0] == 20


@pytest.mark.unit
def test_rank_candidates_excludes_seen_profiles() -> None:
    """Excluded IDs should never appear in response."""
    candidates = [
        RankCandidate(profile_id=10, base_rank=0.5, interests=[1]),
        RankCandidate(profile_id=20, base_rank=0.4, interests=[1]),
    ]

    result = rank_candidates(
        user_id=2,
        user_interest_ids=[1],
        candidates=candidates,
        excluded_ids=[10],
        limit=10,
    )

    assert result == [20]


@pytest.mark.unit
def test_rank_candidates_applies_limit() -> None:
    """Result length should respect requested limit."""
    candidates = [
        RankCandidate(profile_id=10, base_rank=0.3, interests=[]),
        RankCandidate(profile_id=20, base_rank=0.4, interests=[]),
        RankCandidate(profile_id=30, base_rank=0.5, interests=[]),
    ]

    result = rank_candidates(
        user_id=3,
        user_interest_ids=[],
        candidates=candidates,
        excluded_ids=[],
        limit=2,
    )

    assert len(result) == 2
