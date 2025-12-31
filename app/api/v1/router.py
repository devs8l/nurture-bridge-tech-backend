from fastapi import APIRouter

from app.schemas.common import HealthResponse
from app.api.v1.endpoints import auth, tenants, clinical, assessment, email, intake, report

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    email.router,
    prefix="/email",
    tags=["Email"]
)

api_router.include_router(
    tenants.router,
    prefix="/tenants",
    tags=["Tenants"]
)

api_router.include_router(
    clinical.router,
    prefix="/clinical",
    tags=["Clinical"]
)

api_router.include_router(assessment.router, prefix="/assessment", tags=["assessment"])

api_router.include_router(
    intake.router,
    prefix="/intake",
    tags=["Intake"]
)

api_router.include_router(
    report.router,
    prefix="/reports",
    tags=["Reports"]
)

@api_router.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check_placeholder():
    from datetime import datetime
    return {
        "status": "ok",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "dependencies": {
            "database": "connected",
            "redis": "connected"
        }
    }
