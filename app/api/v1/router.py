from fastapi import APIRouter

from app.schemas.common import HealthResponse # we will implement health endpoints properly later
# from app.api.v1.endpoints import auth, users

api_router = APIRouter()

# Example of including sub-routers:
# api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
# api_router.include_router(users.router, prefix="/users", tags=["Users"])

@api_router.get("/health", tags=["System"])
async def health_check_placeholder():
    return {"status": "ok"}
