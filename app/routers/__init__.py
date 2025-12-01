from app.routers.ingredients import router as ingredients_router
from app.routers.food import router as food_router
from app.routers.recipes import router as recipes_router
from app.routers.supplements import router as supplements_router
from app.routers.biomarkers import router as biomarkers_router
from app.routers.exercises import router as exercises_router
from app.routers.targets import router as targets_router
from app.routers.dashboard import router as dashboard_router

__all__ = [
    "ingredients_router",
    "food_router",
    "recipes_router",
    "supplements_router",
    "biomarkers_router",
    "exercises_router",
    "targets_router",
    "dashboard_router",
]
