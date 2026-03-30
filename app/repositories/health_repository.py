from datetime import datetime, timezone


class HealthRepository:
    """Repository for low-level health-related data.

    Stage 1 uses a simple timestamp source; DB-backed probes can be added later.
    """

    @staticmethod
    def utc_now_iso() -> str:
        return datetime.now(tz=timezone.utc).isoformat()
