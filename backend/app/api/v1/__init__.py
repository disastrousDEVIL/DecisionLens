from fastapi import APIRouter

from app.api.v1.routes.compare import router as compare_router
from app.api.v1.routes.providers import router as providers_router

router = APIRouter()
router.include_router(providers_router, prefix="/providers", tags=["providers"])
router.include_router(compare_router, tags=["playground"])

