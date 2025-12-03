import pytest
from datetime import date


@pytest.mark.asyncio
async def test_create_exercise(client, auth_headers):
    """Test create exercise."""
    today = date.today().isoformat()
    data = {
        "date": today,
        "exercise_type": "walk",
        "duration_minutes": 45,
        "details": {
            "miles": 3.2,
            "active_calories": 280,
            "pace_min_per_mile": 14.1,
        },
    }
    response = await client.post("/exercises", json=data, headers=auth_headers)
    assert response.status_code == 201
    result = response.json()
    assert result["exercise_type"] == "walk"
    assert result["duration_minutes"] == 45
    assert result["details"]["miles"] == 3.2


@pytest.mark.asyncio
async def test_create_exercise_no_details(client, auth_headers):
    """Test create exercise without details."""
    today = date.today().isoformat()
    data = {
        "date": today,
        "exercise_type": "weights",
        "duration_minutes": 60,
    }
    response = await client.post("/exercises", json=data, headers=auth_headers)
    assert response.status_code == 201
    result = response.json()
    assert result["details"] is None


@pytest.mark.asyncio
async def test_get_exercises_by_date(client, auth_headers):
    """Test get exercises for a date."""
    today = date.today().isoformat()

    await client.post("/exercises", json={
        "date": today, "exercise_type": "walk", "duration_minutes": 30,
    }, headers=auth_headers)
    await client.post("/exercises", json={
        "date": today, "exercise_type": "weights", "duration_minutes": 45,
    }, headers=auth_headers)

    response = await client.get(f"/exercises?date={today}", headers=auth_headers)
    assert response.status_code == 200
    exercises = response.json()
    assert len(exercises) >= 2


@pytest.mark.asyncio
async def test_get_exercise_history(client, auth_headers):
    """Test get exercise history."""
    today = date.today().isoformat()
    await client.post("/exercises", json={
        "date": today, "exercise_type": "run", "duration_minutes": 30,
    }, headers=auth_headers)

    response = await client.get("/exercises/history?days=7", headers=auth_headers)
    assert response.status_code == 200
    exercises = response.json()
    assert len(exercises) >= 1


@pytest.mark.asyncio
async def test_update_exercise(client, auth_headers):
    """Test update exercise."""
    today = date.today().isoformat()
    response = await client.post("/exercises", json={
        "date": today, "exercise_type": "walk", "duration_minutes": 30,
    }, headers=auth_headers)
    exercise_id = response.json()["id"]

    response = await client.put(
        f"/exercises/{exercise_id}",
        json={"duration_minutes": 45, "details": {"miles": 3.0}},
        headers=auth_headers,
    )
    assert response.status_code == 200
    result = response.json()
    assert result["duration_minutes"] == 45
    assert result["details"]["miles"] == 3.0


@pytest.mark.asyncio
async def test_delete_exercise(client, auth_headers):
    """Test delete exercise."""
    today = date.today().isoformat()
    response = await client.post("/exercises", json={
        "date": today, "exercise_type": "stretch", "duration_minutes": 15,
    }, headers=auth_headers)
    exercise_id = response.json()["id"]

    response = await client.delete(f"/exercises/{exercise_id}", headers=auth_headers)
    assert response.status_code == 204
