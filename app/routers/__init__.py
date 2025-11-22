from .organizations import router as organizations_router
from .employees import router as employees_router
from .dynamic_columns import router as dynamic_columns_router
from .api_keys import router as api_keys_router
from .admin import router as admin_router

__all__ = [
    "organizations_router",
    "employees_router",
    "dynamic_columns_router",
    "api_keys_router",
    "admin_router"
]
