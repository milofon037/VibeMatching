from datetime import UTC, datetime


class HealthRepository:
    """Repository for low-level health-related data.

    Stage 1 uses a simple timestamp source; DB-backed probes can be added later.
    """

    @staticmethod
    def utc_now_iso() -> str:
        return datetime.now(tz=UTC).isoformat()
