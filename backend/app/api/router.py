from fastapi import APIRouter

from app.api.routes import analytics, auth, enterprise, health, inventory, sales

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["authentication"])
api_router.include_router(inventory.router, tags=["inventory"])
api_router.include_router(sales.router, tags=["sales"])
api_router.include_router(analytics.router, tags=["analytics"])
api_router.include_router(enterprise.router, tags=["operations"])
