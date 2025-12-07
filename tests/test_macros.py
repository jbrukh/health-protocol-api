import pytest
from datetime import date


@pytest.mark.asyncio
async def test_get_today_macros(client, auth_headers):
    """Test get today's macros."""
    today = date.today().isoformat()

    await client.post("/foods", json={
        "date": today, "marker": "test", "name": "Test Food",
        "amount": 1, "unit": "x", "calories": 500, "protein_g": 30,
        "carbs_g": 50, "fats_g": 20, "sodium_mg": 500,
    }, headers=auth_headers)

    response = await client.get("/macros/today", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert result["date"] == today
    assert result["totals"]["calories"] >= 500
    assert result["totals"]["protein_g"] >= 30
    assert "targets" in result
    assert "percent_of_min" in result["targets"]["calories"]


@pytest.mark.asyncio
async def test_get_remaining_macros(client, auth_headers):
    """Test get remaining macros."""
    response = await client.get("/macros/remaining", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert "remaining" in result
    assert "calories" in result["remaining"]
    assert "protein_g" in result["remaining"]


@pytest.mark.asyncio
async def test_remaining_with_suggestion(client, auth_headers):
    """Test remaining macros includes suggestion when protein is low."""
    await client.get("/profile", headers=auth_headers)

    response = await client.get("/macros/remaining", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    if result["remaining"]["protein_g"]["min"] > 20:
        assert result["suggestion"] is not None


@pytest.mark.asyncio
async def test_get_macro_history(client, auth_headers):
    """Test get macro history."""
    today = date.today().isoformat()

    await client.post("/foods", json={
        "date": today, "marker": "history_test", "name": "Test Food",
        "amount": 1, "unit": "x", "calories": 300, "protein_g": 20,
        "carbs_g": 30, "fats_g": 10, "sodium_mg": 200,
    }, headers=auth_headers)

    await client.post("/body", json={
        "date": today, "time": "07:00:00", "weight_lbs": 185.0,
    }, headers=auth_headers)

    response = await client.get("/macros/history?limit=7", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert "days" in result
    assert len(result["days"]) == 7
    assert "total_days" in result
    assert "limit" in result
    assert result["limit"] == 7

    today_entry = result["days"][0]
    assert today_entry["date"] == today
    assert "macros" in today_entry
    assert "body" in today_entry


@pytest.mark.asyncio
async def test_macro_percentages(client, auth_headers):
    """Test macro percentages are calculated correctly."""
    today = date.today().isoformat()

    await client.delete(f"/foods/clear?date={today}", headers=auth_headers)

    await client.post("/foods", json={
        "date": today, "marker": "percent_test", "name": "Test Food",
        "amount": 1, "unit": "x", "calories": 900, "protein_g": 75,
        "carbs_g": 75, "fats_g": 25, "sodium_mg": 1150,
    }, headers=auth_headers)

    response = await client.get("/macros/today", headers=auth_headers)
    result = response.json()

    assert result["targets"]["calories"]["percent_of_min"] == 50.0
    assert result["targets"]["protein_g"]["percent_of_min"] == 50.0
    assert result["targets"]["sodium_mg"]["percent_of_max"] == 50.0
