from datetime import UTC, datetime

REFERRAL_BONUS_PER_USER = 0.05
MAX_REFERRAL_BONUS = 0.5
MAX_BASE_RANK_SCORE = 1.7
BEHAVIORAL_LIKES_NORMALIZATION = 20
BEHAVIORAL_LIKES_WEIGHT = 0.4
BEHAVIORAL_LIKE_SKIP_RATIO_WEIGHT = 0.3
BEHAVIORAL_MATCH_RATE_WEIGHT = 0.3
BEHAVIORAL_SCORE_WEIGHT = 0.2


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def normalize_photo_count_score(photo_count: int) -> float:
    return _clamp01(photo_count / 5.0)


def normalize_bio_length_score(bio: str | None) -> float:
    if not bio:
        return 0.0
    return _clamp01(len(bio.strip()) / 500.0)


def normalize_activity_days_score(last_active_at: datetime | None) -> float:
    if last_active_at is None:
        return 0.0

    now = datetime.now(tz=UTC)
    ts = last_active_at
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)

    inactivity_days = max((now - ts).days, 0)
    if inactivity_days >= 30:
        return 0.0
    return _clamp01(1.0 - (inactivity_days / 30.0))


def calculate_referral_bonus(referred_users_count: int) -> float:
    if referred_users_count <= 0:
        return 0.0
    raw_bonus = referred_users_count * REFERRAL_BONUS_PER_USER
    return _clamp(raw_bonus, 0.0, MAX_REFERRAL_BONUS)


def calculate_behavioral_score(
    likes_received_count: int,
    skips_received_count: int,
    matches_count: int,
) -> float:
    likes_volume_score = _clamp01(likes_received_count / BEHAVIORAL_LIKES_NORMALIZATION)

    interactions_count = max(likes_received_count + skips_received_count, 0)
    like_skip_ratio_score = (
        likes_received_count / interactions_count if interactions_count > 0 else 0.0
    )

    match_rate_score = (
        _clamp01(matches_count / likes_received_count) if likes_received_count > 0 else 0.0
    )

    return _clamp01(
        (likes_volume_score * BEHAVIORAL_LIKES_WEIGHT)
        + (like_skip_ratio_score * BEHAVIORAL_LIKE_SKIP_RATIO_WEIGHT)
        + (match_rate_score * BEHAVIORAL_MATCH_RATE_WEIGHT)
    )


def calculate_base_rank(
    photo_count: int,
    bio: str | None,
    last_active_at: datetime | None,
    referred_users_count: int = 0,
    likes_received_count: int = 0,
    skips_received_count: int = 0,
    matches_count: int = 0,
) -> float:
    photo_count_score = normalize_photo_count_score(photo_count)
    bio_length_score = normalize_bio_length_score(bio)
    activity_days_score = normalize_activity_days_score(last_active_at)
    referral_bonus = calculate_referral_bonus(referred_users_count)
    behavioral_score = calculate_behavioral_score(
        likes_received_count=likes_received_count,
        skips_received_count=skips_received_count,
        matches_count=matches_count,
    )

    score = (
        (photo_count_score * 0.2)
        + (bio_length_score * 0.2)
        + (activity_days_score * 0.6)
        + (behavioral_score * BEHAVIORAL_SCORE_WEIGHT)
        + referral_bonus
    )
    return _clamp(score, 0.0, MAX_BASE_RANK_SCORE)
