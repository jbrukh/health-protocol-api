from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import (
    ingredients_router,
    food_router,
    recipes_router,
    targets_router,
    dashboard_router,
    nutrition_labels_router,
)

settings = get_settings()

# Configure OpenAPI servers for Custom GPT integration
servers = []
if settings.openapi_server_url:
    servers.append({"url": settings.openapi_server_url, "description": "Production server"})

app = FastAPI(
    title="Jake's Health Protocol API",
    description="Health tracking API for food, nutrition labels, and recipes. Designed for Custom GPT integration.",
    version="2.1.0",
    servers=servers if servers else None,
)

# CORS middleware for GPT integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api/v1 prefix
API_PREFIX = "/api/v1"

app.include_router(ingredients_router, prefix=API_PREFIX)
app.include_router(food_router, prefix=API_PREFIX)
app.include_router(recipes_router, prefix=API_PREFIX)
app.include_router(targets_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(nutrition_labels_router, prefix=API_PREFIX)


@app.get("/", tags=["Health"], include_in_schema=False)
async def root():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.1.0"}


@app.get("/health", tags=["Health"], include_in_schema=False)
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "2.1.0",
    }
