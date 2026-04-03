from fastapi import APIRouter

from app.api.routes.matches import router as matches_router
from app.api.routes.photos import router as photos_router
from app.api.routes.profiles import router as profiles_router
from app.api.routes.swipes import router as swipes_router
from app.api.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(users_router)
api_router.include_router(profiles_router)
api_router.include_router(photos_router)
api_router.include_router(swipes_router)
api_router.include_router(matches_router)
