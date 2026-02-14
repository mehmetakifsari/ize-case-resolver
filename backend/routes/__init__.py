from .auth import router as auth_router
from .cases import router as cases_router
from .admin import router as admin_router
from .warranty import router as warranty_router
from .site_settings import router as site_settings_router

__all__ = ["auth_router", "cases_router", "admin_router", "warranty_router", "site_settings_router"]
