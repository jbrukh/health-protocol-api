import pytest
from datetime import date


@pytest.mark.asyncio
async def test_get_default_profile(client, auth_headers):
    """Test get profile returns defaults on first call."""
    response = await client.get("/profile", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["birthdate"] is None
    assert data["age"] is None
    assert data["height_inches"] is None
    assert data["targets"]["calories_min"] == 1800
    assert data["targets"]["calories_max"] == 2200
    assert data["targets"]["protein_min_g"] == 150


@pytest.mark.asyncio
async def test_update_profile(client, auth_headers):
    """Test update profile."""
    update_data = {
        "birthdate": "1990-05-15",
        "height_inches": 70,
        "calories_min": 2000,
        "calories_max": 2500,
    }
    response = await client.put("/profile", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["birthdate"] == "1990-05-15"
    assert data["height_inches"] == 70
    assert data["targets"]["calories_min"] == 2000
    assert data["targets"]["calories_max"] == 2500


@pytest.mark.asyncio
async def test_profile_age_calculation(client, auth_headers):
    """Test age is computed from birthdate."""
    today = date.today()
    birth_year = today.year - 30
    update_data = {"birthdate": f"{birth_year}-01-01"}
    response = await client.put("/profile", json=update_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["age"] == 30 or data["age"] == 29


@pytest.mark.asyncio
async def test_partial_profile_update(client, auth_headers):
    """Test partial update only changes specified fields."""
    await client.put("/profile", json={"calories_min": 1900}, headers=auth_headers)

    response = await client.put("/profile", json={"protein_min_g": 160}, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["targets"]["calories_min"] == 1900
    assert data["targets"]["protein_min_g"] == 160
