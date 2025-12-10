import pytest
from datetime import date
from fastapi import HTTPException

from app.database import init_db
from app.models.body import BodyMeasurementCreate, BodyMeasurementUpdate
from app.services import body_service
from app.utils import timezone as tz_utils

@pytest.mark.asyncio
async def test_create_measurement(client, auth_headers):
    """Test create body measurement."""
    today = date.today().isoformat()
    data = {
        "date": today,
        "time": "07:30:00",
        "weight_lbs": 185.5,
        "waist_cm": 86.0,
    }
    response = await client.post("/body", json=data, headers=auth_headers)
    assert response.status_code == 201
    result = response.json()
    assert result["weight_lbs"] == 185.5
    assert result["waist_cm"] == 86.0


@pytest.mark.asyncio
async def test_create_weight_only_measurement(client, auth_headers):
    """Test create measurement with weight only."""
    today = date.today().isoformat()
    data = {
        "date": today,
        "time": "08:00:00",
        "weight_lbs": 186.0,
    }
    response = await client.post("/body", json=data, headers=auth_headers)
    assert response.status_code == 201
    result = response.json()
    assert result["weight_lbs"] == 186.0
    assert result["waist_cm"] is None


@pytest.mark.asyncio
async def test_create_waist_only_measurement(client, auth_headers):
    """Test create measurement with waist only."""
    today = date.today().isoformat()
    data = {
        "date": today,
        "time": "08:30:00",
        "waist_cm": 85.0,
    }
    response = await client.post("/body", json=data, headers=auth_headers)
    assert response.status_code == 201
    result = response.json()
    assert result["weight_lbs"] is None
    assert result["waist_cm"] == 85.0


@pytest.mark.asyncio
async def test_create_measurement_requires_at_least_one(client, auth_headers):
    """Test measurement requires at least one value."""
    today = date.today().isoformat()
    data = {
        "date": today,
        "time": "09:00:00",
    }
    response = await client.post("/body", json=data, headers=auth_headers)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_measurements_by_date(client, auth_headers):
    """Test get measurements for a date."""
    today = date.today().isoformat()

    await client.post("/body", json={
        "date": today, "time": "07:00:00", "weight_lbs": 185.0,
    }, headers=auth_headers)
    await client.post("/body", json={
        "date": today, "time": "19:00:00", "weight_lbs": 186.0,
    }, headers=auth_headers)

    response = await client.get(f"/body?date={today}", headers=auth_headers)
    assert response.status_code == 200
    measurements = response.json()
    assert len(measurements) >= 2


@pytest.mark.asyncio
async def test_get_latest_measurement(client, auth_headers):
    """Test get most recent measurement."""
    today = date.today().isoformat()
    await client.post("/body", json={
        "date": today, "time": "23:59:00", "weight_lbs": 184.0,
    }, headers=auth_headers)

    response = await client.get("/body/latest", headers=auth_headers)
    assert response.status_code == 200
    result = response.json()
    assert result is not None


@pytest.mark.asyncio
async def test_update_measurement(client, auth_headers):
    """Test update measurement."""
    today = date.today().isoformat()
    response = await client.post("/body", json={
        "date": today, "time": "10:00:00", "weight_lbs": 185.0,
    }, headers=auth_headers)
    measurement_id = response.json()["id"]

    response = await client.put(
        f"/body/{measurement_id}",
        json={"weight_lbs": 184.5},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["weight_lbs"] == 184.5


@pytest.mark.asyncio
async def test_delete_measurement(client, auth_headers):
    """Test delete measurement."""
    today = date.today().isoformat()
    response = await client.post("/body", json={
        "date": today, "time": "11:00:00", "weight_lbs": 185.0,
    }, headers=auth_headers)
    measurement_id = response.json()["id"]

    response = await client.delete(f"/body/{measurement_id}", headers=auth_headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_body_default_dates_use_profile_timezone(monkeypatch, client, auth_headers):
    """Default body date range should be based on profile timezone-aware 'today'."""
    target_date = date(2020, 1, 2).isoformat()

    await client.post("/body", json={
        "date": target_date, "time": "07:00:00", "weight_lbs": 180.0,
    }, headers=auth_headers)

    from app.routers import body as body_router
    monkeypatch.setattr(body_router, "current_date_in_timezone", lambda tz: date.fromisoformat(target_date))

    response = await client.get("/body", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert any(m["date"] == target_date for m in data["measurements"])


@pytest.mark.asyncio
async def test_update_delete_respect_db_path(tmp_path):
    """Update/delete should honor explicit db_path instead of default database."""
    db_path = tmp_path / "alt_body.db"
    await init_db(str(db_path))

    created = await body_service.create_measurement(
        BodyMeasurementCreate(
            date=date(2024, 1, 1),
            time="08:00:00",
            weight_lbs=180.0,
        ),
        db_path=str(db_path),
    )

    updated = await body_service.update_measurement(
        created.id,
        BodyMeasurementUpdate(weight_lbs=181.5),
        db_path=str(db_path),
    )
    assert updated.weight_lbs == 181.5

    await body_service.delete_measurement(created.id, db_path=str(db_path))
    with pytest.raises(HTTPException):
        await body_service.get_measurement(created.id, db_path=str(db_path))
