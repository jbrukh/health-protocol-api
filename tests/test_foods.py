import pytest
from datetime import date


@pytest.mark.asyncio
async def test_create_food(client, auth_headers):
    """Test create food entry directly."""
    today = date.today().isoformat()
    data = {
        "date": today,
        "marker": "breakfast_eggs",
        "name": "Scrambled Eggs",
        "amount": 2,
        "unit": "large",
        "calories": 140,
        "protein_g": 12,
        "carbs_g": 1,
        "fats_g": 10,
        "sodium_mg": 140,
    }
    response = await client.post("/foods", json=data, headers=auth_headers)
    assert response.status_code == 201
    result = response.json()
    assert result["name"] == "Scrambled Eggs"
    assert result["calories"] == 140


@pytest.mark.asyncio
async def test_create_foods_from_recipe(client, auth_headers, sample_recipe):
    """Test create foods from recipe expands to individual entries."""
    today = date.today().isoformat()
    data = {
        "recipe_id": sample_recipe["id"],
        "date": today,
        "marker": "breakfast_shake",
        "scale": 1.0,
    }
    response = await client.post("/foods/from-recipe", json=data, headers=auth_headers)
    assert response.status_code == 201
    result = response.json()
    assert len(result) == 3
    assert all(f["marker"] == "breakfast_shake" for f in result)
    assert all(f["recipe_id"] == sample_recipe["id"] for f in result)


@pytest.mark.asyncio
async def test_create_foods_from_recipe_scaled(client, auth_headers, sample_recipe):
    """Test recipe expansion with scale."""
    today = date.today().isoformat()
    data = {
        "recipe_id": sample_recipe["id"],
        "date": today,
        "marker": "half_shake",
        "scale": 0.5,
    }
    response = await client.post("/foods/from-recipe", json=data, headers=auth_headers)
    assert response.status_code == 201
    result = response.json()
    total_calories = sum(f["calories"] for f in result)
    expected_calories = sum(i["calories"] for i in sample_recipe["items"]) // 2
    assert abs(total_calories - expected_calories) <= 3


@pytest.mark.asyncio
async def test_get_foods_by_date(client, auth_headers):
    """Test get foods by date."""
    today = date.today().isoformat()
    data = {
        "date": today,
        "marker": "test",
        "name": "Test Food",
        "amount": 1,
        "unit": "serving",
        "calories": 100,
        "protein_g": 10,
        "carbs_g": 10,
        "fats_g": 5,
        "sodium_mg": 50,
    }
    await client.post("/foods", json=data, headers=auth_headers)

    response = await client.get(f"/foods?date={today}", headers=auth_headers)
    assert response.status_code == 200
    foods = response.json()
    assert len(foods) >= 1


@pytest.mark.asyncio
async def test_get_foods_by_marker(client, auth_headers):
    """Test filter foods by marker."""
    today = date.today().isoformat()

    await client.post("/foods", json={
        "date": today, "marker": "breakfast", "name": "Food 1",
        "amount": 1, "unit": "x", "calories": 100, "protein_g": 10,
        "carbs_g": 10, "fats_g": 5, "sodium_mg": 50,
    }, headers=auth_headers)

    await client.post("/foods", json={
        "date": today, "marker": "lunch", "name": "Food 2",
        "amount": 1, "unit": "x", "calories": 200, "protein_g": 20,
        "carbs_g": 20, "fats_g": 10, "sodium_mg": 100,
    }, headers=auth_headers)

    response = await client.get(f"/foods?date={today}&marker=breakfast", headers=auth_headers)
    assert response.status_code == 200
    foods = response.json()
    assert all(f["marker"] == "breakfast" for f in foods)


@pytest.mark.asyncio
async def test_delete_food(client, auth_headers):
    """Test delete food entry."""
    today = date.today().isoformat()
    data = {
        "date": today, "marker": "delete_test", "name": "Delete Me",
        "amount": 1, "unit": "x", "calories": 100, "protein_g": 10,
        "carbs_g": 10, "fats_g": 5, "sodium_mg": 50,
    }
    response = await client.post("/foods", json=data, headers=auth_headers)
    food_id = response.json()["id"]

    response = await client.delete(f"/foods/{food_id}", headers=auth_headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_foods_by_marker(client, auth_headers):
    """Test delete all foods with marker."""
    today = date.today().isoformat()

    for i in range(3):
        await client.post("/foods", json={
            "date": today, "marker": "batch_delete", "name": f"Food {i}",
            "amount": 1, "unit": "x", "calories": 100, "protein_g": 10,
            "carbs_g": 10, "fats_g": 5, "sodium_mg": 50,
        }, headers=auth_headers)

    response = await client.delete(
        f"/foods/by-marker?date={today}&marker=batch_delete",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["deleted"] == 3


@pytest.mark.asyncio
async def test_clear_foods_by_date(client, auth_headers):
    """Test clear all foods for a date."""
    today = date.today().isoformat()

    for i in range(3):
        await client.post("/foods", json={
            "date": today, "marker": f"clear_{i}", "name": f"Food {i}",
            "amount": 1, "unit": "x", "calories": 100, "protein_g": 10,
            "carbs_g": 10, "fats_g": 5, "sodium_mg": 50,
        }, headers=auth_headers)

    response = await client.delete(f"/foods/clear?date={today}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["deleted"] >= 3
