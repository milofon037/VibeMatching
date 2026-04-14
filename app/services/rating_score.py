from datetime import UTC, datetime


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


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


def calculate_base_rank(
    photo_count: int,
    bio: str | None,
    last_active_at: datetime | None,
) -> float:
    photo_count_score = normalize_photo_count_score(photo_count)
    bio_length_score = normalize_bio_length_score(bio)
    activity_days_score = normalize_activity_days_score(last_active_at)

    score = (photo_count_score * 0.2) + (bio_length_score * 0.2) + (activity_days_score * 0.6)
    return _clamp01(score)
