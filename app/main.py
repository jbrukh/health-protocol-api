from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import profile, ingredients, recipes, foods, macros, body, exercises, supplements, phases, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Health Tracker API",
    description="A lightweight REST API for food, macro, exercise, and body measurement tracking.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile.router, prefix="/profile", tags=["Profile"])
app.include_router(ingredients.router, prefix="/ingredients", tags=["Ingredients"])
app.include_router(recipes.router, prefix="/recipes", tags=["Recipes"])
app.include_router(foods.router, prefix="/foods", tags=["Foods"])
app.include_router(macros.router, prefix="/macros", tags=["Macros"])
app.include_router(body.router, prefix="/body", tags=["Body Measurements"])
app.include_router(exercises.router, prefix="/exercises", tags=["Exercises"])
app.include_router(supplements.router, prefix="/supplements", tags=["Supplements"])
app.include_router(phases.router, prefix="/phases", tags=["Phases"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])


@app.get("/health")
async def health_check():
    """Health check endpoint (no auth required)."""
    return {"status": "healthy"}
