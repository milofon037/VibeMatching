from fastapi import APIRouter

from app.repositories.health_repository import HealthRepository
from app.services.health_service import HealthService

router = APIRouter(tags=["health"])

health_service = HealthService(repository=HealthRepository())


@router.get("/health")
async def healthcheck() -> dict:
    return health_service.get_health_payload()
