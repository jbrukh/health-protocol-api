import pytest
from datetime import date


@pytest.mark.asyncio
async def test_full_flow_ingredient_to_macros(client, auth_headers):
    """Test full flow: create ingredient -> create recipe -> log recipe -> check macros."""
    today = date.today().isoformat()

    ingredient_response = await client.post("/ingredients", json={
        "name": "Integration Test Protein",
        "default_amount": 1,
        "default_unit": "scoop",
        "calories": 100,
        "protein_g": 20,
        "carbs_g": 5,
        "fats_g": 2,
        "sodium_mg": 100,
    }, headers=auth_headers)
    ingredient = ingredient_response.json()

    recipe_response = await client.post("/recipes", json={
        "name": "Integration Test Recipe",
        "items": [
            {"ingredient_id": ingredient["id"], "amount": 2, "unit": "scoop"},
        ],
    }, headers=auth_headers)
    recipe = recipe_response.json()
    assert recipe["totals"]["calories"] == 200
    assert recipe["totals"]["protein_g"] == 40

    foods_response = await client.post("/foods/from-recipe", json={
        "recipe_id": recipe["id"],
        "date": today,
        "marker": "integration_test",
        "scale": 1.0,
    }, headers=auth_headers)
    foods = foods_response.json()
    assert len(foods) == 1

    macros_response = await client.get("/macros/today", headers=auth_headers)
    macros = macros_response.json()
    assert macros["totals"]["calories"] >= 200
    assert macros["totals"]["protein_g"] >= 40


@pytest.mark.asyncio
async def test_delete_flow(client, auth_headers):
    """Test delete flow: log foods -> delete by marker -> verify totals change."""
    today = date.today().isoformat()

    await client.delete(f"/foods/clear?date={today}", headers=auth_headers)

    for i in range(3):
        await client.post("/foods", json={
            "date": today, "marker": "delete_flow_test", "name": f"Food {i}",
            "amount": 1, "unit": "x", "calories": 100, "protein_g": 10,
            "carbs_g": 10, "fats_g": 5, "sodium_mg": 50,
        }, headers=auth_headers)

    macros_before = await client.get("/macros/today", headers=auth_headers)
    before_calories = macros_before.json()["totals"]["calories"]
    assert before_calories >= 300

    await client.delete(
        f"/foods/by-marker?date={today}&marker=delete_flow_test",
        headers=auth_headers,
    )

    macros_after = await client.get("/macros/today", headers=auth_headers)
    after_calories = macros_after.json()["totals"]["calories"]
    assert after_calories == before_calories - 300


@pytest.mark.asyncio
async def test_history_flow(client, auth_headers):
    """Test history flow: log multiple days -> request history -> verify data."""
    today = date.today().isoformat()

    await client.post("/foods", json={
        "date": today, "marker": "history_flow", "name": "Today Food",
        "amount": 1, "unit": "x", "calories": 500, "protein_g": 40,
        "carbs_g": 50, "fats_g": 20, "sodium_mg": 300,
    }, headers=auth_headers)

    await client.post("/body", json={
        "date": today, "time": "07:00:00", "weight_lbs": 180.0, "waist_cm": 85.0,
    }, headers=auth_headers)

    history_response = await client.get("/macros/history?limit=7", headers=auth_headers)
    history = history_response.json()

    assert len(history["days"]) == 7
    assert history["limit"] == 7

    today_data = history["days"][0]
    assert today_data["date"] == today
    assert today_data["macros"]["calories"] >= 500
    assert today_data["body"] is not None
    assert today_data["body"]["weight_lbs"] == 180.0


@pytest.mark.asyncio
async def test_recipe_update_affects_new_logs_only(client, auth_headers):
    """Test updating recipe doesn't affect existing food logs (immutable snapshots)."""
    today = date.today().isoformat()

    ingredient_response = await client.post("/ingredients", json={
        "name": "Immutable Test Ingredient",
        "default_amount": 1,
        "default_unit": "serving",
        "calories": 100,
        "protein_g": 10,
        "carbs_g": 10,
        "fats_g": 5,
        "sodium_mg": 50,
    }, headers=auth_headers)
    ingredient = ingredient_response.json()

    recipe_response = await client.post("/recipes", json={
        "name": "Immutable Test Recipe",
        "items": [
            {"ingredient_id": ingredient["id"], "amount": 1, "unit": "serving"},
        ],
    }, headers=auth_headers)
    recipe = recipe_response.json()

    foods_response = await client.post("/foods/from-recipe", json={
        "recipe_id": recipe["id"],
        "date": today,
        "marker": "immutable_test",
        "scale": 1.0,
    }, headers=auth_headers)
    original_food = foods_response.json()[0]
    original_calories = original_food["calories"]

    await client.put(
        f"/ingredients/{ingredient['id']}",
        json={"calories": 200},
        headers=auth_headers,
    )

    logged_food = await client.get(f"/foods/{original_food['id']}", headers=auth_headers)
    assert logged_food.json()["calories"] == original_calories
