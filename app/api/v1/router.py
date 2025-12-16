from fastapi import APIRouter

from app.schemas.common import HealthResponse
from app.api.v1.endpoints import auth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])

@api_router.get("/health", tags=["System"])
async def health_check_placeholder():
    return {"status": "ok"}
