import os
import tempfile
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Set environment variables BEFORE importing app modules
TEST_TOKEN = "test-token"
os.environ["API_TOKEN"] = TEST_TOKEN

from app.database import init_db, get_db, SCHEMA
from app.config import settings


@pytest.fixture(scope="function")
def test_db_path(tmp_path):
    """Create a temporary database file for each test."""
    db_file = tmp_path / "test.db"
    return str(db_file)


@pytest_asyncio.fixture(scope="function")
async def test_db(test_db_path, monkeypatch):
    """Initialize test database and patch settings."""
    # Patch settings to use test database
    monkeypatch.setattr(settings, "database_path", test_db_path)
    monkeypatch.setattr(settings, "api_token", TEST_TOKEN)

    # Initialize the database
    await init_db(test_db_path)

    yield test_db_path


@pytest_asyncio.fixture(scope="function")
async def client(test_db):
    """Create test client with initialized database."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers():
    """Auth headers for requests."""
    return {"Authorization": f"Bearer {TEST_TOKEN}"}


@pytest_asyncio.fixture
async def sample_ingredient(client, auth_headers):
    """Create a sample ingredient."""
    data = {
        "name": "Whey Protein",
        "default_amount": 1,
        "default_unit": "scoop",
        "calories": 120,
        "protein_g": 24,
        "carbs_g": 3,
        "fats_g": 1,
        "sodium_mg": 50,
    }
    response = await client.post("/ingredients", json=data, headers=auth_headers)
    return response.json()


@pytest_asyncio.fixture
async def sample_ingredients(client, auth_headers):
    """Create multiple sample ingredients."""
    ingredients_data = [
        {
            "name": "Whey Protein",
            "default_amount": 1,
            "default_unit": "scoop",
            "calories": 120,
            "protein_g": 24,
            "carbs_g": 3,
            "fats_g": 1,
            "sodium_mg": 50,
        },
        {
            "name": "Almond Milk",
            "default_amount": 1,
            "default_unit": "cup",
            "calories": 30,
            "protein_g": 1,
            "carbs_g": 1,
            "fats_g": 2.5,
            "sodium_mg": 180,
        },
        {
            "name": "Banana",
            "default_amount": 1,
            "default_unit": "medium",
            "calories": 105,
            "protein_g": 1.3,
            "carbs_g": 27,
            "fats_g": 0.4,
            "sodium_mg": 1,
        },
    ]
    ingredients = []
    for data in ingredients_data:
        response = await client.post("/ingredients", json=data, headers=auth_headers)
        ingredients.append(response.json())
    return ingredients


@pytest_asyncio.fixture
async def sample_recipe(client, auth_headers, sample_ingredients):
    """Create a sample recipe with items."""
    data = {
        "name": "Protein Shake",
        "items": [
            {"ingredient_id": sample_ingredients[0]["id"], "amount": 1, "unit": "scoop"},
            {"ingredient_id": sample_ingredients[1]["id"], "amount": 1.5, "unit": "cup"},
            {"ingredient_id": sample_ingredients[2]["id"], "amount": 1, "unit": "medium"},
        ],
    }
    response = await client.post("/recipes", json=data, headers=auth_headers)
    return response.json()
