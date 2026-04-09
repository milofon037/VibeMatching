from app.core.config import settings
from app.repositories.health_repository import HealthRepository


class HealthService:
    """Service layer for health endpoint payload."""

    def __init__(self, repository: HealthRepository) -> None:
        self.repository = repository

    def get_health_payload(self) -> dict:
        return {
            "status": settings.health_status_ok,
            "service": settings.service_name,
            "timestamp": self.repository.utc_now_iso(),
        }
