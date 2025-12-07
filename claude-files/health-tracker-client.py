"""
Health Tracker API Python Client

A complete Python client for interacting with the Health Tracker API.
Designed for use by Claude or any Python application.

Usage:
    from health_tracker_client import HealthTrackerClient

    client = HealthTrackerClient(
        base_url="https://health-tracker-api-production.up.railway.app",
        api_token="your-api-token"
    )

    # Get today's macros
    macros = client.get_macros_today()

    # Log food
    client.create_food(
        date="2024-01-15",
        marker="lunch",
        name="Grilled Chicken",
        amount=6,
        unit="oz",
        calories=280,
        protein_g=52,
        carbs_g=0,
        fats_g=6
    )
"""

from dataclasses import dataclass
from datetime import date, time, datetime
from typing import Any, Optional
import json
import urllib.request
import urllib.error
import urllib.parse


@dataclass
class APIResponse:
    """Response from the API."""
    success: bool
    status_code: int
    data: Any = None
    error: Optional[str] = None


class HealthTrackerClient:
    """Python client for the Health Tracker API."""

    def __init__(self, base_url: str, api_token: str):
        """
        Initialize the client.

        Args:
            base_url: API base URL (e.g., "https://health-tracker-api-production.up.railway.app")
            api_token: Bearer token for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None
    ) -> APIResponse:
        """Make an HTTP request to the API."""
        url = f"{self.base_url}{path}"

        if params:
            query = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            if query:
                url = f"{url}?{query}"

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        body = json.dumps(data).encode("utf-8") if data else None

        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                status_code = response.status
                if status_code == 204:
                    return APIResponse(success=True, status_code=status_code, data=None)
                response_data = json.loads(response.read().decode("utf-8"))
                return APIResponse(success=True, status_code=status_code, data=response_data)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            try:
                error_data = json.loads(error_body)
                error_msg = error_data.get("detail", str(error_data))
            except:
                error_msg = error_body or str(e)
            return APIResponse(success=False, status_code=e.code, error=error_msg)
        except urllib.error.URLError as e:
            return APIResponse(success=False, status_code=0, error=str(e.reason))

    def _get(self, path: str, params: Optional[dict] = None) -> APIResponse:
        return self._request("GET", path, params=params)

    def _post(self, path: str, data: Optional[dict] = None) -> APIResponse:
        return self._request("POST", path, data=data)

    def _put(self, path: str, data: Optional[dict] = None) -> APIResponse:
        return self._request("PUT", path, data=data)

    def _delete(self, path: str, params: Optional[dict] = None) -> APIResponse:
        return self._request("DELETE", path, params=params)

    # ==================== Profile ====================

    def get_profile(self) -> APIResponse:
        """Get user profile with computed age and targets."""
        return self._get("/profile")

    def update_profile(
        self,
        birthdate: Optional[str] = None,
        height_inches: Optional[float] = None,
        calories_min: Optional[int] = None,
        calories_max: Optional[int] = None,
        protein_min_g: Optional[int] = None,
        protein_max_g: Optional[int] = None,
        carbs_min_g: Optional[int] = None,
        carbs_max_g: Optional[int] = None,
        fats_min_g: Optional[int] = None,
        fats_max_g: Optional[int] = None,
        sodium_max_mg: Optional[int] = None
    ) -> APIResponse:
        """Update user profile."""
        data = {k: v for k, v in {
            "birthdate": birthdate,
            "height_inches": height_inches,
            "calories_min": calories_min,
            "calories_max": calories_max,
            "protein_min_g": protein_min_g,
            "protein_max_g": protein_max_g,
            "carbs_min_g": carbs_min_g,
            "carbs_max_g": carbs_max_g,
            "fats_min_g": fats_min_g,
            "fats_max_g": fats_max_g,
            "sodium_max_mg": sodium_max_mg,
        }.items() if v is not None}
        return self._put("/profile", data)

    # ==================== Ingredients ====================

    def list_ingredients(self) -> APIResponse:
        """List all ingredients."""
        return self._get("/ingredients")

    def search_ingredients(self, query: str) -> APIResponse:
        """Search ingredients by name."""
        return self._get("/ingredients/search", params={"q": query})

    def get_ingredient(self, ingredient_id: int) -> APIResponse:
        """Get ingredient by ID."""
        return self._get(f"/ingredients/{ingredient_id}")

    def create_ingredient(
        self,
        name: str,
        default_amount: float,
        default_unit: str,
        calories: int,
        protein_g: float,
        carbs_g: float,
        fats_g: float,
        sodium_mg: int = 0
    ) -> APIResponse:
        """Create a new ingredient."""
        return self._post("/ingredients", {
            "name": name,
            "default_amount": default_amount,
            "default_unit": default_unit,
            "calories": calories,
            "protein_g": protein_g,
            "carbs_g": carbs_g,
            "fats_g": fats_g,
            "sodium_mg": sodium_mg,
        })

    def update_ingredient(
        self,
        ingredient_id: int,
        name: Optional[str] = None,
        default_amount: Optional[float] = None,
        default_unit: Optional[str] = None,
        calories: Optional[int] = None,
        protein_g: Optional[float] = None,
        carbs_g: Optional[float] = None,
        fats_g: Optional[float] = None,
        sodium_mg: Optional[int] = None
    ) -> APIResponse:
        """Update an ingredient."""
        data = {k: v for k, v in {
            "name": name,
            "default_amount": default_amount,
            "default_unit": default_unit,
            "calories": calories,
            "protein_g": protein_g,
            "carbs_g": carbs_g,
            "fats_g": fats_g,
            "sodium_mg": sodium_mg,
        }.items() if v is not None}
        return self._put(f"/ingredients/{ingredient_id}", data)

    def delete_ingredient(self, ingredient_id: int) -> APIResponse:
        """Delete an ingredient."""
        return self._delete(f"/ingredients/{ingredient_id}")

    # ==================== Recipes ====================

    def list_recipes(self) -> APIResponse:
        """List all recipes with computed totals."""
        return self._get("/recipes")

    def get_recipe(self, recipe_id: int) -> APIResponse:
        """Get recipe by ID with items and totals."""
        return self._get(f"/recipes/{recipe_id}")

    def create_recipe(
        self,
        name: str,
        items: Optional[list[dict]] = None
    ) -> APIResponse:
        """
        Create a new recipe.

        Args:
            name: Recipe name
            items: List of items, each with ingredient_id, amount, unit
        """
        return self._post("/recipes", {
            "name": name,
            "items": items or [],
        })

    def update_recipe(self, recipe_id: int, name: str) -> APIResponse:
        """Update recipe name."""
        return self._put(f"/recipes/{recipe_id}", {"name": name})

    def delete_recipe(self, recipe_id: int) -> APIResponse:
        """Delete a recipe."""
        return self._delete(f"/recipes/{recipe_id}")

    def add_recipe_item(
        self,
        recipe_id: int,
        ingredient_id: int,
        amount: float,
        unit: str
    ) -> APIResponse:
        """Add an item to a recipe."""
        return self._post(f"/recipes/{recipe_id}/items", {
            "ingredient_id": ingredient_id,
            "amount": amount,
            "unit": unit,
        })

    def update_recipe_item(
        self,
        recipe_id: int,
        item_id: int,
        amount: Optional[float] = None,
        unit: Optional[str] = None
    ) -> APIResponse:
        """Update a recipe item."""
        data = {k: v for k, v in {"amount": amount, "unit": unit}.items() if v is not None}
        return self._put(f"/recipes/{recipe_id}/items/{item_id}", data)

    def delete_recipe_item(self, recipe_id: int, item_id: int) -> APIResponse:
        """Remove an item from a recipe."""
        return self._delete(f"/recipes/{recipe_id}/items/{item_id}")

    # ==================== Foods ====================

    def get_foods(self, date: str, marker: Optional[str] = None) -> APIResponse:
        """
        Get food entries for a date.

        Args:
            date: Date in YYYY-MM-DD format
            marker: Optional meal marker to filter by (e.g., "breakfast", "lunch")
        """
        return self._get("/foods", params={"date": date, "marker": marker})

    def get_food(self, food_id: int) -> APIResponse:
        """Get food entry by ID."""
        return self._get(f"/foods/{food_id}")

    def create_food(
        self,
        date: str,
        marker: str,
        name: str,
        amount: float,
        unit: str,
        calories: int,
        protein_g: float,
        carbs_g: float,
        fats_g: float,
        sodium_mg: int = 0
    ) -> APIResponse:
        """
        Log a food entry.

        Args:
            date: Date in YYYY-MM-DD format
            marker: Meal marker (e.g., "breakfast", "lunch", "dinner", "snack")
            name: Food name
            amount: Quantity consumed
            unit: Unit of measurement
            calories: Total calories
            protein_g: Grams of protein
            carbs_g: Grams of carbohydrates
            fats_g: Grams of fat
            sodium_mg: Milligrams of sodium (default 0)
        """
        return self._post("/foods", {
            "date": date,
            "marker": marker,
            "name": name,
            "amount": amount,
            "unit": unit,
            "calories": calories,
            "protein_g": protein_g,
            "carbs_g": carbs_g,
            "fats_g": fats_g,
            "sodium_mg": sodium_mg,
        })

    def create_food_from_recipe(
        self,
        recipe_id: int,
        date: str,
        marker: str,
        scale: float = 1.0
    ) -> APIResponse:
        """
        Log foods from a recipe.

        Args:
            recipe_id: ID of the recipe
            date: Date in YYYY-MM-DD format
            marker: Meal marker
            scale: Scale factor (1.0 = full recipe, 0.5 = half, etc.)
        """
        return self._post("/foods/from-recipe", {
            "recipe_id": recipe_id,
            "date": date,
            "marker": marker,
            "scale": scale,
        })

    def update_food(
        self,
        food_id: int,
        marker: Optional[str] = None,
        name: Optional[str] = None,
        amount: Optional[float] = None,
        unit: Optional[str] = None,
        calories: Optional[int] = None,
        protein_g: Optional[float] = None,
        carbs_g: Optional[float] = None,
        fats_g: Optional[float] = None,
        sodium_mg: Optional[int] = None
    ) -> APIResponse:
        """Update a food entry."""
        data = {k: v for k, v in {
            "marker": marker,
            "name": name,
            "amount": amount,
            "unit": unit,
            "calories": calories,
            "protein_g": protein_g,
            "carbs_g": carbs_g,
            "fats_g": fats_g,
            "sodium_mg": sodium_mg,
        }.items() if v is not None}
        return self._put(f"/foods/{food_id}", data)

    def delete_food(self, food_id: int) -> APIResponse:
        """Delete a food entry."""
        return self._delete(f"/foods/{food_id}")

    def delete_foods_by_marker(self, date: str, marker: str) -> APIResponse:
        """Delete all food entries with a specific marker on a date."""
        return self._delete("/foods/by-marker", params={"date": date, "marker": marker})

    def clear_foods(self, date: str) -> APIResponse:
        """Clear all food entries for a date."""
        return self._delete("/foods/clear", params={"date": date})

    # ==================== Macros ====================

    def get_macros_today(self) -> APIResponse:
        """Get today's macro totals with target percentages."""
        return self._get("/macros/today")

    def get_macros_remaining(self) -> APIResponse:
        """Get remaining macro budget for today."""
        return self._get("/macros/remaining")

    def get_macros_history(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> APIResponse:
        """
        Get macro and body measurement history for a date range with pagination.
        Defaults to last 30 days if no dates provided.

        Args:
            start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
            end_date: End date in YYYY-MM-DD format (default: today)
            limit: Max days to return (1-1000, default 100)
            offset: Days to skip (default 0)
        """
        params = {"limit": limit, "offset": offset}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self._get("/macros/history", params=params)

    # ==================== Body Measurements ====================

    def get_body_measurements(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> APIResponse:
        """
        Get body measurements for a date range with pagination.
        Defaults to last 30 days if no dates provided.

        Args:
            start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
            end_date: End date in YYYY-MM-DD format (default: today)
            limit: Max records to return (1-1000, default 100)
            offset: Records to skip (default 0)
        """
        params = {"limit": limit, "offset": offset}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self._get("/body", params=params)

    def get_body_summary(self) -> APIResponse:
        """Get summary of all body measurements (earliest date, latest date, total count)."""
        return self._get("/body/summary")

    def get_latest_body_measurement(self) -> APIResponse:
        """Get the most recent body measurement."""
        return self._get("/body/latest")

    def get_body_measurement(self, measurement_id: int) -> APIResponse:
        """Get body measurement by ID."""
        return self._get(f"/body/{measurement_id}")

    def create_body_measurement(
        self,
        date: str,
        time: str,
        weight_lbs: Optional[float] = None,
        waist_cm: Optional[float] = None,
        fat_mass_lbs: Optional[float] = None,
        muscle_mass_lbs: Optional[float] = None,
        bone_mass_lbs: Optional[float] = None,
        body_water_pct: Optional[float] = None,
        source: str = "manual"
    ) -> APIResponse:
        """
        Log a body measurement.

        Note: At least one of weight_lbs or waist_cm must be provided.

        Args:
            date: Date in YYYY-MM-DD format
            time: Time in HH:MM:SS format
            weight_lbs: Weight in pounds
            waist_cm: Waist circumference in centimeters
            fat_mass_lbs: Fat mass in pounds
            muscle_mass_lbs: Muscle mass in pounds
            bone_mass_lbs: Bone mass in pounds
            body_water_pct: Body water percentage
            source: Data source (default "manual")
        """
        data = {"date": date, "time": time, "source": source}
        if weight_lbs is not None:
            data["weight_lbs"] = weight_lbs
        if waist_cm is not None:
            data["waist_cm"] = waist_cm
        if fat_mass_lbs is not None:
            data["fat_mass_lbs"] = fat_mass_lbs
        if muscle_mass_lbs is not None:
            data["muscle_mass_lbs"] = muscle_mass_lbs
        if bone_mass_lbs is not None:
            data["bone_mass_lbs"] = bone_mass_lbs
        if body_water_pct is not None:
            data["body_water_pct"] = body_water_pct
        return self._post("/body", data)

    def update_body_measurement(
        self,
        measurement_id: int,
        date: Optional[str] = None,
        time: Optional[str] = None,
        weight_lbs: Optional[float] = None,
        waist_cm: Optional[float] = None,
        fat_mass_lbs: Optional[float] = None,
        muscle_mass_lbs: Optional[float] = None,
        bone_mass_lbs: Optional[float] = None,
        body_water_pct: Optional[float] = None
    ) -> APIResponse:
        """Update a body measurement."""
        data = {k: v for k, v in {
            "date": date,
            "time": time,
            "weight_lbs": weight_lbs,
            "waist_cm": waist_cm,
            "fat_mass_lbs": fat_mass_lbs,
            "muscle_mass_lbs": muscle_mass_lbs,
            "bone_mass_lbs": bone_mass_lbs,
            "body_water_pct": body_water_pct,
        }.items() if v is not None}
        return self._put(f"/body/{measurement_id}", data)

    def delete_body_measurement(self, measurement_id: int) -> APIResponse:
        """Delete a body measurement."""
        return self._delete(f"/body/{measurement_id}")

    # ==================== Exercises ====================

    def get_exercises(self, date: str) -> APIResponse:
        """Get exercises for a date."""
        return self._get("/exercises", params={"date": date})

    def get_exercise(self, exercise_id: int) -> APIResponse:
        """Get exercise by ID."""
        return self._get(f"/exercises/{exercise_id}")

    def get_exercise_history(self, days: int = 7) -> APIResponse:
        """
        Get exercise history.

        Args:
            days: Number of days to look back (default 7)
        """
        return self._get("/exercises/history", params={"days": days})

    def create_exercise(
        self,
        date: str,
        exercise_type: str,
        duration_minutes: int,
        details: Optional[dict] = None
    ) -> APIResponse:
        """
        Log an exercise.

        Args:
            date: Date in YYYY-MM-DD format
            exercise_type: Type of exercise (e.g., "strength training", "running")
            duration_minutes: Duration in minutes (max 1440)
            details: Optional dict with additional details
        """
        data = {
            "date": date,
            "exercise_type": exercise_type,
            "duration_minutes": duration_minutes,
        }
        if details:
            data["details"] = details
        return self._post("/exercises", data)

    def update_exercise(
        self,
        exercise_id: int,
        date: Optional[str] = None,
        exercise_type: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        details: Optional[dict] = None
    ) -> APIResponse:
        """Update an exercise."""
        data = {k: v for k, v in {
            "date": date,
            "exercise_type": exercise_type,
            "duration_minutes": duration_minutes,
            "details": details,
        }.items() if v is not None}
        return self._put(f"/exercises/{exercise_id}", data)

    def delete_exercise(self, exercise_id: int) -> APIResponse:
        """Delete an exercise."""
        return self._delete(f"/exercises/{exercise_id}")

    # ==================== Supplements ====================

    def list_supplements(
        self,
        active: Optional[bool] = None,
        time_of_day: Optional[str] = None
    ) -> APIResponse:
        """
        List supplements with optional filters.

        Args:
            active: Filter by active status
            time_of_day: Filter by time (morning, midday, afternoon, evening, bedtime)
        """
        return self._get("/supplements", params={"active": active, "time_of_day": time_of_day})

    def get_active_supplements(self) -> APIResponse:
        """Get all currently active supplements."""
        return self._get("/supplements/active")

    def get_supplement_schedule(self) -> APIResponse:
        """Get today's supplement schedule organized by time of day."""
        return self._get("/supplements/schedule")

    def get_supplement_history(self, start_date: str, end_date: str) -> APIResponse:
        """
        Get supplements that were active during a date range.

        Args:
            start_date: Range start in YYYY-MM-DD format
            end_date: Range end in YYYY-MM-DD format
        """
        return self._get("/supplements/history", params={
            "start_date": start_date,
            "end_date": end_date,
        })

    def get_supplement(self, supplement_id: int) -> APIResponse:
        """Get supplement by ID."""
        return self._get(f"/supplements/{supplement_id}")

    def create_supplement(
        self,
        name: str,
        dosage_amount: float,
        dosage_unit: str,
        purpose: str,
        time_of_day: str,
        start_date: str,
        with_food: bool = False,
        notes: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> APIResponse:
        """
        Create a supplement entry.

        Args:
            name: Supplement name
            dosage_amount: Dosage quantity
            dosage_unit: Unit (e.g., "mg", "IU", "mcg")
            purpose: Purpose/reason for taking
            time_of_day: When to take (morning, midday, afternoon, evening, bedtime)
            start_date: Start date in YYYY-MM-DD format
            with_food: Whether to take with food
            notes: Additional notes
            end_date: Optional end date in YYYY-MM-DD format
        """
        data = {
            "name": name,
            "dosage_amount": dosage_amount,
            "dosage_unit": dosage_unit,
            "purpose": purpose,
            "time_of_day": time_of_day,
            "start_date": start_date,
            "with_food": with_food,
        }
        if notes:
            data["notes"] = notes
        if end_date:
            data["end_date"] = end_date
        return self._post("/supplements", data)

    def update_supplement(
        self,
        supplement_id: int,
        name: Optional[str] = None,
        dosage_amount: Optional[float] = None,
        dosage_unit: Optional[str] = None,
        purpose: Optional[str] = None,
        time_of_day: Optional[str] = None,
        with_food: Optional[bool] = None,
        notes: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> APIResponse:
        """Update a supplement."""
        data = {k: v for k, v in {
            "name": name,
            "dosage_amount": dosage_amount,
            "dosage_unit": dosage_unit,
            "purpose": purpose,
            "time_of_day": time_of_day,
            "with_food": with_food,
            "notes": notes,
            "start_date": start_date,
            "end_date": end_date,
        }.items() if v is not None}
        return self._put(f"/supplements/{supplement_id}", data)

    def delete_supplement(self, supplement_id: int) -> APIResponse:
        """Delete a supplement."""
        return self._delete(f"/supplements/{supplement_id}")

    # ==================== Phases ====================

    def list_phases(self) -> APIResponse:
        """List all phases."""
        return self._get("/phases")

    def get_active_phases(self) -> APIResponse:
        """Get active and upcoming phases."""
        return self._get("/phases/active")

    def get_phase(self, phase_id: int) -> APIResponse:
        """Get phase by ID."""
        return self._get(f"/phases/{phase_id}")

    def create_phase(
        self,
        name: str,
        description: str,
        start_date: str,
        end_date: str,
        is_recurring: bool = False,
        recurrence_interval_days: Optional[int] = None
    ) -> APIResponse:
        """
        Create a phase.

        Args:
            name: Phase name
            description: Phase description
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            is_recurring: Whether the phase repeats
            recurrence_interval_days: Days between recurrences
        """
        data = {
            "name": name,
            "description": description,
            "start_date": start_date,
            "end_date": end_date,
            "is_recurring": is_recurring,
        }
        if recurrence_interval_days:
            data["recurrence_interval_days"] = recurrence_interval_days
        return self._post("/phases", data)

    def update_phase(
        self,
        phase_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        is_recurring: Optional[bool] = None,
        recurrence_interval_days: Optional[int] = None
    ) -> APIResponse:
        """Update a phase."""
        data = {k: v for k, v in {
            "name": name,
            "description": description,
            "start_date": start_date,
            "end_date": end_date,
            "is_recurring": is_recurring,
            "recurrence_interval_days": recurrence_interval_days,
        }.items() if v is not None}
        return self._put(f"/phases/{phase_id}", data)

    def delete_phase(self, phase_id: int) -> APIResponse:
        """Delete a phase."""
        return self._delete(f"/phases/{phase_id}")

    # ==================== Blood Pressure ====================

    def get_blood_pressure(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> APIResponse:
        """
        Get blood pressure readings for a date range with pagination.
        Defaults to last 30 days if no dates provided.

        Args:
            start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
            end_date: End date in YYYY-MM-DD format (default: today)
            limit: Max records to return (1-1000, default 100)
            offset: Records to skip (default 0)
        """
        params = {"limit": limit, "offset": offset}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self._get("/blood-pressure", params=params)

    def get_blood_pressure_summary(self) -> APIResponse:
        """Get summary of all blood pressure readings (earliest date, latest date, total count)."""
        return self._get("/blood-pressure/summary")

    def get_latest_blood_pressure(self) -> APIResponse:
        """Get most recent blood pressure reading."""
        return self._get("/blood-pressure/latest")

    # Note: Blood pressure data is synced from Withings. Manual create/delete not supported.

    # ==================== Activity ====================

    def get_activity(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> APIResponse:
        """
        Get daily activity for a date range with pagination.
        Defaults to last 30 days if no dates provided.

        Args:
            start_date: Start date in YYYY-MM-DD format (default: 30 days ago)
            end_date: End date in YYYY-MM-DD format (default: today)
            limit: Max records to return (1-1000, default 100)
            offset: Records to skip (default 0)
        """
        params = {"limit": limit, "offset": offset}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self._get("/activity", params=params)

    def get_activity_summary(self) -> APIResponse:
        """Get summary of all daily activity (earliest date, latest date, total count)."""
        return self._get("/activity/summary")

    def get_latest_activity(self) -> APIResponse:
        """Get most recent daily activity."""
        return self._get("/activity/latest")

    # Note: Activity data is synced from Withings. Manual create/delete not supported.

    # ==================== Sleep ====================

    def get_sleep(self, date: Optional[str] = None) -> APIResponse:
        """
        Get sleep data for a date.

        Args:
            date: Date in YYYY-MM-DD format (default: today)
        """
        params = {"date": date} if date else {}
        return self._get("/sleep", params=params)

    def get_latest_sleep(self) -> APIResponse:
        """Get most recent sleep entry."""
        return self._get("/sleep/latest")

    # Note: Sleep data is synced from Withings. Manual create/delete not supported.

    # ==================== Withings ====================

    def get_withings_auth_url(self) -> APIResponse:
        """Get Withings OAuth authorization URL."""
        return self._get("/withings/auth")

    def get_withings_status(self) -> APIResponse:
        """Check Withings connection status."""
        return self._get("/withings/status")

    def refresh_withings_token(self) -> APIResponse:
        """Force Withings token refresh."""
        return self._post("/withings/refresh")

    def disconnect_withings(self) -> APIResponse:
        """Disconnect Withings integration."""
        return self._delete("/withings/disconnect")

    def backfill_withings(self, start_date: str, end_date: str) -> APIResponse:
        """
        Trigger manual Withings historical data backfill.

        Args:
            start_date: Range start in YYYY-MM-DD format
            end_date: Range end in YYYY-MM-DD format
        """
        return self._post("/withings/backfill", {
            "start_date": start_date,
            "end_date": end_date,
        })


# ==================== Convenience Functions ====================

def create_client(base_url: str, api_token: str) -> HealthTrackerClient:
    """Create a Health Tracker API client."""
    return HealthTrackerClient(base_url, api_token)


def create_production_client(api_token: str) -> HealthTrackerClient:
    """Create a client for the production API."""
    return HealthTrackerClient("https://health-tracker-api-production.up.railway.app", api_token)
