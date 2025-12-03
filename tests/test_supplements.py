import pytest
from datetime import date, timedelta


@pytest.mark.asyncio
async def test_create_supplement(client, auth_headers):
    """Test create supplement."""
    today = date.today().isoformat()
    data = {
        "name": "Vitamin D3",
        "dosage": "5000 IU",
        "purpose": "Vitamin D supplementation",
        "time_of_day": "morning",
        "with_food": True,
        "notes": "Take with fatty meal for better absorption",
        "start_date": today,
    }
    response = await client.post("/supplements", json=data, headers=auth_headers)
    assert response.status_code == 201
    result = response.json()
    assert result["name"] == "Vitamin D3"
    assert result["dosage"] == "5000 IU"
    assert result["time_of_day"] == "morning"
    assert result["with_food"] is True
    assert result["is_active"] is True


@pytest.mark.asyncio
async def test_create_supplement_minimal(client, auth_headers):
    """Test create supplement with minimal fields."""
    today = date.today().isoformat()
    data = {
        "name": "Fish Oil",
        "dosage": "1000mg",
        "purpose": "Omega-3",
        "time_of_day": "evening",
        "start_date": today,
    }
    response = await client.post("/supplements", json=data, headers=auth_headers)
    assert response.status_code == 201
    result = response.json()
    assert result["name"] == "Fish Oil"
    assert result["with_food"] is False
    assert result["notes"] is None
    assert result["end_date"] is None


@pytest.mark.asyncio
async def test_create_supplement_with_end_date(client, auth_headers):
    """Test create supplement with end date (not active after end)."""
    past_start = (date.today() - timedelta(days=30)).isoformat()
    past_end = (date.today() - timedelta(days=1)).isoformat()
    data = {
        "name": "Antibiotic",
        "dosage": "500mg",
        "purpose": "Treatment",
        "time_of_day": "morning",
        "start_date": past_start,
        "end_date": past_end,
    }
    response = await client.post("/supplements", json=data, headers=auth_headers)
    assert response.status_code == 201
    result = response.json()
    assert result["is_active"] is False


@pytest.mark.asyncio
async def test_get_supplement(client, auth_headers):
    """Test get supplement by ID."""
    today = date.today().isoformat()
    response = await client.post("/supplements", json={
        "name": "Magnesium",
        "dosage": "400mg",
        "purpose": "Sleep support",
        "time_of_day": "bedtime",
        "start_date": today,
    }, headers=auth_headers)
    supplement_id = response.json()["id"]

    response = await client.get(f"/supplements/{supplement_id}", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert result["name"] == "Magnesium"


@pytest.mark.asyncio
async def test_get_supplement_not_found(client, auth_headers):
    """Test get supplement that doesn't exist."""
    response = await client.get("/supplements/99999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_supplements(client, auth_headers):
    """Test list all supplements."""
    today = date.today().isoformat()
    await client.post("/supplements", json={
        "name": "Vitamin C",
        "dosage": "1000mg",
        "purpose": "Immune support",
        "time_of_day": "morning",
        "start_date": today,
    }, headers=auth_headers)
    await client.post("/supplements", json={
        "name": "Zinc",
        "dosage": "30mg",
        "purpose": "Immune support",
        "time_of_day": "evening",
        "start_date": today,
    }, headers=auth_headers)

    response = await client.get("/supplements", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert "supplements" in result
    assert len(result["supplements"]) >= 2


@pytest.mark.asyncio
async def test_list_supplements_filter_active(client, auth_headers):
    """Test list supplements with active filter."""
    today = date.today().isoformat()
    past_end = (date.today() - timedelta(days=1)).isoformat()
    past_start = (date.today() - timedelta(days=10)).isoformat()

    # Active supplement
    await client.post("/supplements", json={
        "name": "Active Supp",
        "dosage": "100mg",
        "purpose": "Test",
        "time_of_day": "morning",
        "start_date": today,
    }, headers=auth_headers)
    # Inactive supplement
    await client.post("/supplements", json={
        "name": "Inactive Supp",
        "dosage": "100mg",
        "purpose": "Test",
        "time_of_day": "morning",
        "start_date": past_start,
        "end_date": past_end,
    }, headers=auth_headers)

    response = await client.get("/supplements?active=true", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    for supp in result["supplements"]:
        assert supp["is_active"] is True


@pytest.mark.asyncio
async def test_list_supplements_filter_time_of_day(client, auth_headers):
    """Test list supplements filtered by time of day."""
    today = date.today().isoformat()
    await client.post("/supplements", json={
        "name": "Morning Supp",
        "dosage": "100mg",
        "purpose": "Test",
        "time_of_day": "morning",
        "start_date": today,
    }, headers=auth_headers)
    await client.post("/supplements", json={
        "name": "Bedtime Supp",
        "dosage": "100mg",
        "purpose": "Test",
        "time_of_day": "bedtime",
        "start_date": today,
    }, headers=auth_headers)

    response = await client.get("/supplements?time_of_day=morning", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    for supp in result["supplements"]:
        assert supp["time_of_day"] == "morning"


@pytest.mark.asyncio
async def test_get_active_supplements(client, auth_headers):
    """Test get active supplements endpoint."""
    today = date.today().isoformat()
    await client.post("/supplements", json={
        "name": "Active Test",
        "dosage": "100mg",
        "purpose": "Test",
        "time_of_day": "morning",
        "start_date": today,
    }, headers=auth_headers)

    response = await client.get("/supplements/active", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert "supplements" in result
    for supp in result["supplements"]:
        assert supp["is_active"] is True


@pytest.mark.asyncio
async def test_get_supplement_schedule(client, auth_headers):
    """Test get supplement schedule organized by time of day."""
    today = date.today().isoformat()
    await client.post("/supplements", json={
        "name": "Morning Vitamin",
        "dosage": "100mg",
        "purpose": "Test",
        "time_of_day": "morning",
        "start_date": today,
    }, headers=auth_headers)
    await client.post("/supplements", json={
        "name": "Bedtime Mineral",
        "dosage": "200mg",
        "purpose": "Test",
        "time_of_day": "bedtime",
        "start_date": today,
    }, headers=auth_headers)

    response = await client.get("/supplements/schedule", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert "date" in result
    assert "schedule" in result
    assert "morning" in result["schedule"]
    assert "bedtime" in result["schedule"]
    assert "summary" in result
    assert "total_supplements" in result["summary"]


@pytest.mark.asyncio
async def test_get_supplement_history(client, auth_headers):
    """Test get supplement history for date range."""
    today = date.today()
    start = (today - timedelta(days=30)).isoformat()
    end = today.isoformat()

    await client.post("/supplements", json={
        "name": "History Test",
        "dosage": "100mg",
        "purpose": "Test",
        "time_of_day": "morning",
        "start_date": start,
    }, headers=auth_headers)

    response = await client.get(
        f"/supplements/history?start_date={start}&end_date={end}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    result = response.json()
    assert "supplements" in result
    assert "start_date" in result
    assert "end_date" in result


@pytest.mark.asyncio
async def test_update_supplement(client, auth_headers):
    """Test update supplement."""
    today = date.today().isoformat()
    response = await client.post("/supplements", json={
        "name": "Update Test",
        "dosage": "100mg",
        "purpose": "Test",
        "time_of_day": "morning",
        "start_date": today,
    }, headers=auth_headers)
    supplement_id = response.json()["id"]

    response = await client.put(
        f"/supplements/{supplement_id}",
        json={"dosage": "200mg", "notes": "Updated dose"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    result = response.json()
    assert result["dosage"] == "200mg"
    assert result["notes"] == "Updated dose"


@pytest.mark.asyncio
async def test_update_supplement_not_found(client, auth_headers):
    """Test update supplement that doesn't exist."""
    response = await client.put(
        "/supplements/99999",
        json={"dosage": "200mg"},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_supplement(client, auth_headers):
    """Test delete supplement."""
    today = date.today().isoformat()
    response = await client.post("/supplements", json={
        "name": "Delete Test",
        "dosage": "100mg",
        "purpose": "Test",
        "time_of_day": "morning",
        "start_date": today,
    }, headers=auth_headers)
    supplement_id = response.json()["id"]

    response = await client.delete(f"/supplements/{supplement_id}", headers=auth_headers)
    assert response.status_code == 204

    response = await client.get(f"/supplements/{supplement_id}", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_supplement_not_found(client, auth_headers):
    """Test delete supplement that doesn't exist."""
    response = await client.delete("/supplements/99999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_time_of_day(client, auth_headers):
    """Test create supplement with invalid time_of_day."""
    today = date.today().isoformat()
    data = {
        "name": "Invalid Test",
        "dosage": "100mg",
        "purpose": "Test",
        "time_of_day": "invalid_time",
        "start_date": today,
    }
    response = await client.post("/supplements", json=data, headers=auth_headers)
    assert response.status_code == 422  # Validation error
