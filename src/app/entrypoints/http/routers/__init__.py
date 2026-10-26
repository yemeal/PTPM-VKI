from app.entrypoints.http.routers.comments import router as comments_router
from app.entrypoints.http.routers.health import router as health_router
from app.entrypoints.http.routers.root import router as root_router

__all__ = ["comments_router", "health_router", "root_router"]
