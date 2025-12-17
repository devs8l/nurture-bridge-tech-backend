from fastapi import APIRouter

from app.schemas.common import HealthResponse
from app.api.v1.endpoints import auth, tenants, assessment

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(assessment.router, prefix="/assessment", tags=["assessment"])

@api_router.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check_placeholder():
    return {"status": "ok"}
