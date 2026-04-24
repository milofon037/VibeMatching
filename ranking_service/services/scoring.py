from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256

from ranking_service.domain.schemas import RankCandidate


def _deterministic_jitter(user_id: int, profile_id: int, day_seed: str) -> float:
    token = f"{user_id}:{profile_id}:{day_seed}".encode()
    digest = sha256(token).hexdigest()
    bucket = int(digest[:8], 16) / 0xFFFFFFFF
    return bucket * 0.05


def _interests_match_score(user_interest_ids: list[int], candidate_interest_ids: list[int]) -> float:
    if not user_interest_ids or not candidate_interest_ids:
        return 0.0
    user_set = set(user_interest_ids)
    candidate_set = set(candidate_interest_ids)
    overlap = len(user_set.intersection(candidate_set))
    denominator = max(len(user_set), 1)
    return overlap / denominator


def rank_candidates(
    user_id: int,
    user_interest_ids: list[int],
    candidates: list[RankCandidate],
    excluded_ids: list[int],
    limit: int,
) -> list[int]:
    excluded = set(excluded_ids)
    day_seed = datetime.now(tz=UTC).strftime("%Y-%m-%d")

    scored: list[tuple[int, float]] = []
    for candidate in candidates:
        if candidate.profile_id in excluded:
            continue

        interests_match = _interests_match_score(user_interest_ids, candidate.interests)
        score = (candidate.base_rank * 0.5) + (interests_match * 0.5)
        score += _deterministic_jitter(user_id=user_id, profile_id=candidate.profile_id, day_seed=day_seed)
        scored.append((candidate.profile_id, score))

    scored.sort(key=lambda item: item[1], reverse=True)
    return [profile_id for profile_id, _ in scored[:limit]]
