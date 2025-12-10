import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.logging_config import configure_logging
from app.routers import (
    profile, ingredients, recipes, foods, macros, body, exercises,
    supplements, phases, admin, withings, blood_pressure, activity, sleep
)


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

# Configure logging (JSON to stdout for Railway compatibility)
configure_logging()

# CORS configuration - use environment variable for allowed origins
# Default to restrictive setting; set CORS_ORIGINS="*" in dev if needed
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env == "*":
    cors_origins = ["*"]
elif cors_origins_env:
    cors_origins = [origin.strip() for origin in cors_origins_env.split(",")]
else:
    # Default: no CORS (same-origin only)
    cors_origins = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
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
app.include_router(withings.router, prefix="/withings", tags=["Withings"])
app.include_router(blood_pressure.router, prefix="/blood-pressure", tags=["Blood Pressure"])
app.include_router(activity.router, prefix="/activity", tags=["Activity"])
app.include_router(sleep.router, prefix="/sleep", tags=["Sleep"])


@app.get("/health")
async def health_check():
    """Health check endpoint (no auth required)."""
    return {"status": "healthy"}
