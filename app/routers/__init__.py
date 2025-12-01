from app.routers.ingredients import router as ingredients_router
from app.routers.food import router as food_router
from app.routers.recipes import router as recipes_router
from app.routers.targets import router as targets_router
from app.routers.dashboard import router as dashboard_router
from app.routers.nutrition_labels import router as nutrition_labels_router
from app.routers.admin import router as admin_router

__all__ = [
    "ingredients_router",
    "food_router",
    "recipes_router",
    "targets_router",
    "dashboard_router",
    "nutrition_labels_router",
    "admin_router",
]
