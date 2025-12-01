"""API tests for biomarkers endpoints."""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient


class TestBiomarkersAPI:
    @pytest.fixture
    async def sample_biomarkers(self, client: AsyncClient, api_headers: dict) -> list:
        """Create sample biomarker readings."""
        now = datetime.utcnow()
        readings = [
            {
                "name": "Total Cholesterol",
                "value": 200,
                "unit": "mg/dL",
                "measured_at": (now - timedelta(days=90)).isoformat(),
                "notes": "Baseline",
            },
            {
                "name": "Total Cholesterol",
                "value": 185,
                "unit": "mg/dL",
                "measured_at": (now - timedelta(days=30)).isoformat(),
            },
            {
                "name": "Total Cholesterol",
                "value": 175,
                "unit": "mg/dL",
                "measured_at": now.isoformat(),
                "notes": "After diet change",
            },
            {
                "name": "Vitamin D",
                "value": 30,
                "unit": "ng/mL",
                "measured_at": now.isoformat(),
            },
        ]
        created = []
        for reading in readings:
            response = await client.post(
                "/api/v1/biomarkers", json=reading, headers=api_headers
            )
            created.append(response.json())
        return created

    async def test_create_biomarker(self, client: AsyncClient, api_headers: dict):
        """Test creating a biomarker reading."""
        data = {
            "name": "Blood Glucose",
            "value": 95,
            "unit": "mg/dL",
            "measured_at": datetime.utcnow().isoformat(),
            "notes": "Fasting",
        }
        response = await client.post("/api/v1/biomarkers", json=data, headers=api_headers)

        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "Blood Glucose"
        assert result["value"] == 95
        assert result["id"] is not None

    async def test_get_biomarker_history(
        self, client: AsyncClient, api_headers: dict, sample_biomarkers: list
    ):
        """Test getting history for a specific biomarker."""
        response = await client.get(
            "/api/v1/biomarkers",
            params={"name": "Total Cholesterol"},
            headers=api_headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert len(result) == 3
        # Should be in descending order by measured_at
        assert result[0]["value"] == 175  # Most recent

    async def test_get_latest_biomarkers(
        self, client: AsyncClient, api_headers: dict, sample_biomarkers: list
    ):
        """Test getting latest reading for all biomarkers."""
        response = await client.get("/api/v1/biomarkers/latest", headers=api_headers)

        assert response.status_code == 200
        result = response.json()
        # Should have 2 unique biomarkers
        assert len(result) == 2
        names = [r["name"] for r in result]
        assert "Total Cholesterol" in names
        assert "Vitamin D" in names

    async def test_compare_biomarker(
        self, client: AsyncClient, api_headers: dict, sample_biomarkers: list
    ):
        """Test comparing biomarker over time."""
        now = datetime.utcnow()
        start = (now - timedelta(days=100)).isoformat()
        end = now.isoformat()

        response = await client.get(
            "/api/v1/biomarkers/compare",
            params={"name": "Total Cholesterol", "start": start, "end": end},
            headers=api_headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Total Cholesterol"
        assert result["unit"] == "mg/dL"
        assert len(result["readings"]) == 3
        assert result["min_value"] == 175
        assert result["max_value"] == 200
        assert result["change"] == -25  # 175 - 200
        assert result["change_percent"] == -12.5  # -25/200 * 100

    async def test_compare_biomarker_no_readings(
        self, client: AsyncClient, api_headers: dict
    ):
        """Test compare with no readings in range."""
        now = datetime.utcnow()
        start = (now - timedelta(days=10)).isoformat()
        end = (now - timedelta(days=5)).isoformat()

        response = await client.get(
            "/api/v1/biomarkers/compare",
            params={"name": "Nonexistent", "start": start, "end": end},
            headers=api_headers,
        )

        assert response.status_code == 404
