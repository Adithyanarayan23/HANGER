from fastapi import APIRouter
from app.core.config import settings

api_router = APIRouter()


@api_router.get("/", tags=["API v1"])
async def get_api_v1_info():
    """Return API v1 version metadata."""
    return {
        "message": f"{settings.APP_NAME} API v1",
        "version": settings.APP_VERSION,
    }
