"""Routes module for API endpoints."""

from .analytics import router as analytics_router
from .auth import router as auth_router
from .debug import router as debug_router
from .history import router as history_router
from .profile import router as profile_router
from .workspace import router as workspace_router

__all__ = [
    "analytics_router",
    "auth_router",
    "debug_router",
    "history_router",
    "profile_router",
    "workspace_router",
]
