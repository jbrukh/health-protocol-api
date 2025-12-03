import pytest
from datetime import date, timedelta


@pytest.mark.asyncio
async def test_create_phase(client, auth_headers):
    """Test create phase."""
    today = date.today()
    start = today.isoformat()
    end = (today + timedelta(days=30)).isoformat()
    data = {
        "name": "Cutting Phase",
        "description": "Caloric deficit for fat loss",
        "start_date": start,
        "end_date": end,
        "is_recurring": False,
    }
    response = await client.post("/phases", json=data, headers=auth_headers)
    assert response.status_code == 201
    result = response.json()
    assert result["name"] == "Cutting Phase"
    assert result["description"] == "Caloric deficit for fat loss"
    assert result["is_active"] is True
    assert result["days_remaining"] == 30


@pytest.mark.asyncio
async def test_create_phase_recurring(client, auth_headers):
    """Test create recurring phase."""
    today = date.today()
    start = today.isoformat()
    end = (today + timedelta(days=7)).isoformat()
    data = {
        "name": "Fasting Week",
        "description": "Intermittent fasting protocol",
        "start_date": start,
        "end_date": end,
        "is_recurring": True,
        "recurrence_interval_days": 30,
    }
    response = await client.post("/phases", json=data, headers=auth_headers)
    assert response.status_code == 201
    result = response.json()
    assert result["is_recurring"] is True
    assert result["recurrence_interval_days"] == 30


@pytest.mark.asyncio
async def test_create_phase_past(client, auth_headers):
    """Test create phase in the past (not active)."""
    past_start = (date.today() - timedelta(days=30)).isoformat()
    past_end = (date.today() - timedelta(days=1)).isoformat()
    data = {
        "name": "Past Phase",
        "description": "A completed phase",
        "start_date": past_start,
        "end_date": past_end,
    }
    response = await client.post("/phases", json=data, headers=auth_headers)
    assert response.status_code == 201
    result = response.json()
    assert result["is_active"] is False
    assert result["days_remaining"] is None


@pytest.mark.asyncio
async def test_get_phase(client, auth_headers):
    """Test get phase by ID."""
    today = date.today()
    response = await client.post("/phases", json={
        "name": "Test Phase",
        "description": "Test",
        "start_date": today.isoformat(),
        "end_date": (today + timedelta(days=14)).isoformat(),
    }, headers=auth_headers)
    phase_id = response.json()["id"]

    response = await client.get(f"/phases/{phase_id}", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert result["name"] == "Test Phase"


@pytest.mark.asyncio
async def test_get_phase_not_found(client, auth_headers):
    """Test get phase that doesn't exist."""
    response = await client.get("/phases/99999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_phases(client, auth_headers):
    """Test list all phases."""
    today = date.today()
    await client.post("/phases", json={
        "name": "Phase 1",
        "description": "First phase",
        "start_date": today.isoformat(),
        "end_date": (today + timedelta(days=30)).isoformat(),
    }, headers=auth_headers)
    await client.post("/phases", json={
        "name": "Phase 2",
        "description": "Second phase",
        "start_date": (today + timedelta(days=31)).isoformat(),
        "end_date": (today + timedelta(days=60)).isoformat(),
    }, headers=auth_headers)

    response = await client.get("/phases", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert "phases" in result
    assert len(result["phases"]) >= 2


@pytest.mark.asyncio
async def test_list_phases_filter_active(client, auth_headers):
    """Test list phases with active filter."""
    today = date.today()
    # Active phase
    await client.post("/phases", json={
        "name": "Active Phase",
        "description": "Currently active",
        "start_date": today.isoformat(),
        "end_date": (today + timedelta(days=30)).isoformat(),
    }, headers=auth_headers)
    # Inactive phase
    await client.post("/phases", json={
        "name": "Inactive Phase",
        "description": "In the past",
        "start_date": (today - timedelta(days=30)).isoformat(),
        "end_date": (today - timedelta(days=1)).isoformat(),
    }, headers=auth_headers)

    response = await client.get("/phases?active=true", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    for phase in result["phases"]:
        assert phase["is_active"] is True


@pytest.mark.asyncio
async def test_list_phases_exclude_past(client, auth_headers):
    """Test list phases excluding past phases."""
    today = date.today()
    # Future phase
    await client.post("/phases", json={
        "name": "Future Phase",
        "description": "Coming up",
        "start_date": (today + timedelta(days=1)).isoformat(),
        "end_date": (today + timedelta(days=30)).isoformat(),
    }, headers=auth_headers)
    # Past phase
    await client.post("/phases", json={
        "name": "Past Phase",
        "description": "Already done",
        "start_date": (today - timedelta(days=30)).isoformat(),
        "end_date": (today - timedelta(days=1)).isoformat(),
    }, headers=auth_headers)

    response = await client.get("/phases?include_past=false", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    for phase in result["phases"]:
        assert phase["end_date"] >= today.isoformat()


@pytest.mark.asyncio
async def test_get_active_phases(client, auth_headers):
    """Test get active phases with upcoming phases."""
    today = date.today()
    # Active phase
    await client.post("/phases", json={
        "name": "Current Phase",
        "description": "Active now",
        "start_date": today.isoformat(),
        "end_date": (today + timedelta(days=14)).isoformat(),
    }, headers=auth_headers)
    # Upcoming phase (within 7 days)
    await client.post("/phases", json={
        "name": "Upcoming Phase",
        "description": "Starting soon",
        "start_date": (today + timedelta(days=3)).isoformat(),
        "end_date": (today + timedelta(days=10)).isoformat(),
    }, headers=auth_headers)

    response = await client.get("/phases/active", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert "date" in result
    assert "active_phases" in result
    assert "upcoming_phases" in result
    assert "total_active" in result
    assert "total_upcoming" in result
    assert result["total_active"] >= 1


@pytest.mark.asyncio
async def test_update_phase(client, auth_headers):
    """Test update phase."""
    today = date.today()
    response = await client.post("/phases", json={
        "name": "Update Test",
        "description": "Original description",
        "start_date": today.isoformat(),
        "end_date": (today + timedelta(days=14)).isoformat(),
    }, headers=auth_headers)
    phase_id = response.json()["id"]

    response = await client.put(
        f"/phases/{phase_id}",
        json={"description": "Updated description", "is_recurring": True},
        headers=auth_headers,
    )
    assert response.status_code == 200
    result = response.json()
    assert result["description"] == "Updated description"
    assert result["is_recurring"] is True


@pytest.mark.asyncio
async def test_update_phase_dates(client, auth_headers):
    """Test update phase dates."""
    today = date.today()
    response = await client.post("/phases", json={
        "name": "Date Update Test",
        "description": "Test",
        "start_date": today.isoformat(),
        "end_date": (today + timedelta(days=14)).isoformat(),
    }, headers=auth_headers)
    phase_id = response.json()["id"]

    new_end = (today + timedelta(days=30)).isoformat()
    response = await client.put(
        f"/phases/{phase_id}",
        json={"end_date": new_end},
        headers=auth_headers,
    )
    assert response.status_code == 200
    result = response.json()
    assert result["end_date"] == new_end
    assert result["days_remaining"] == 30


@pytest.mark.asyncio
async def test_update_phase_not_found(client, auth_headers):
    """Test update phase that doesn't exist."""
    response = await client.put(
        "/phases/99999",
        json={"description": "Updated"},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_phase(client, auth_headers):
    """Test delete phase."""
    today = date.today()
    response = await client.post("/phases", json={
        "name": "Delete Test",
        "description": "To be deleted",
        "start_date": today.isoformat(),
        "end_date": (today + timedelta(days=7)).isoformat(),
    }, headers=auth_headers)
    phase_id = response.json()["id"]

    response = await client.delete(f"/phases/{phase_id}", headers=auth_headers)
    assert response.status_code == 204

    response = await client.get(f"/phases/{phase_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_phase_not_found(client, auth_headers):
    """Test delete phase that doesn't exist."""
    response = await client.delete("/phases/99999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_phase_days_remaining_calculation(client, auth_headers):
    """Test that days_remaining is correctly calculated."""
    today = date.today()
    days_ahead = 10
    response = await client.post("/phases", json={
        "name": "Days Test",
        "description": "Testing days_remaining",
        "start_date": today.isoformat(),
        "end_date": (today + timedelta(days=days_ahead)).isoformat(),
    }, headers=auth_headers)
    assert response.status_code == 201
    result = response.json()
    assert result["days_remaining"] == days_ahead


@pytest.mark.asyncio
async def test_upcoming_phase_days_until_start(client, auth_headers):
    """Test that days_until_start is correctly calculated for upcoming phases."""
    today = date.today()
    days_ahead = 5
    await client.post("/phases", json={
        "name": "Upcoming Test",
        "description": "Testing days_until_start",
        "start_date": (today + timedelta(days=days_ahead)).isoformat(),
        "end_date": (today + timedelta(days=days_ahead + 7)).isoformat(),
    }, headers=auth_headers)

    response = await client.get("/phases/active", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    # Find our upcoming phase
    upcoming = [p for p in result["upcoming_phases"] if p["name"] == "Upcoming Test"]
    assert len(upcoming) == 1
    assert upcoming[0]["days_until_start"] == days_ahead
