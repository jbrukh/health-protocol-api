"""
Integration tests for Custom GPT use cases.
Run with: pytest tests/test_use_cases.py -v

Uses the test fixtures from conftest.py which:
- Uses SQLite in-memory database
- Creates/drops tables for each test
- Overrides auth to use test API key
"""
import pytest
from datetime import date, timedelta


class TestUseCase1_LogNaturalLanguageFood:
    """
    Use Case 1: User says "I've eaten two eggs and a slice of white bread."
    GPT figures out macros, creates ingredients, logs them, user can see daily summary.
    """

    @pytest.mark.asyncio
    async def test_log_eggs_and_bread(self, client, api_headers):
        # Step 1: GPT creates ingredients with estimated macros
        egg = await client.post(
            "/api/v1/ingredients",
            headers=api_headers,
            json={
                "name": "Egg (large)",
                "serving_size": 50,
                "serving_unit": "g",
                "protein_g": 6.3,
                "carbs_g": 0.4,
                "fat_g": 5.0,
                "sodium_mg": 62,
                "calories": 72,
            },
        )
        assert egg.status_code == 201
        egg_id = egg.json()["id"]

        bread = await client.post(
            "/api/v1/ingredients",
            headers=api_headers,
            json={
                "name": "White Bread (slice)",
                "serving_size": 30,
                "serving_unit": "g",
                "protein_g": 2.7,
                "carbs_g": 14.3,
                "fat_g": 0.8,
                "sodium_mg": 142,
                "calories": 75,
            },
        )
        assert bread.status_code == 201
        bread_id = bread.json()["id"]

        # Step 2: GPT logs 2 eggs
        today = date.today().isoformat()
        log1 = await client.post(
            "/api/v1/food",
            headers=api_headers,
            json={
                "date": today,
                "ingredient_id": egg_id,
                "quantity": 2,  # 2 eggs
                "unit": "serving",
                "meal_label": "breakfast",
            },
        )
        assert log1.status_code == 201
        # Should auto-calculate: 2 * 72 = 144 calories

        # Step 3: GPT logs 1 slice of bread
        log2 = await client.post(
            "/api/v1/food",
            headers=api_headers,
            json={
                "date": today,
                "ingredient_id": bread_id,
                "quantity": 1,
                "unit": "serving",
                "meal_label": "breakfast",
            },
        )
        assert log2.status_code == 201

        # Step 4: User asks for today's summary
        summary = await client.get(
            f"/api/v1/food/summary?date={today}",
            headers=api_headers,
        )
        assert summary.status_code == 200
        data = summary.json()

        # Verify totals: 2 eggs + 1 bread
        assert data["total_calories"] == pytest.approx(144 + 75, rel=0.1)
        assert data["total_protein_g"] == pytest.approx(12.6 + 2.7, rel=0.1)
        assert data["entry_count"] == 2


class TestUseCase2_WeeklyHistoryForAdvice:
    """
    Use Case 2: User asks for advice on what to eat next.
    GPT queries last 7 days of macro data to give informed suggestions.
    """

    @pytest.mark.asyncio
    async def test_get_weekly_history(self, client, api_headers):
        # Create an ingredient
        chicken = await client.post(
            "/api/v1/ingredients",
            headers=api_headers,
            json={
                "name": "Chicken Breast",
                "serving_size": 100,
                "serving_unit": "g",
                "protein_g": 31,
                "carbs_g": 0,
                "fat_g": 3.6,
                "sodium_mg": 74,
                "calories": 165,
            },
        )
        chicken_id = chicken.json()["id"]

        # Log food for multiple days
        for i in range(7):
            day = (date.today() - timedelta(days=i)).isoformat()
            await client.post(
                "/api/v1/food",
                headers=api_headers,
                json={
                    "date": day,
                    "ingredient_id": chicken_id,
                    "quantity": 200,
                    "unit": "g",
                    "meal_label": "dinner",
                },
            )

        # Query last 7 days
        end_date = date.today().isoformat()
        start_date = (date.today() - timedelta(days=6)).isoformat()

        history = await client.get(
            f"/api/v1/food/history?start={start_date}&end={end_date}",
            headers=api_headers,
        )
        assert history.status_code == 200
        data = history.json()

        # Should have 7 days of data
        assert len(data) == 7

        # Each day should have ~330 calories (200g chicken)
        for day_data in data:
            assert day_data["total_calories"] == pytest.approx(330, rel=0.1)
            assert day_data["total_protein_g"] == pytest.approx(62, rel=0.1)
            assert "total_carbs_g" in day_data
            assert "total_fat_g" in day_data
            assert "total_sodium_mg" in day_data


class TestUseCase3_UpdateFoodWithActualLabel:
    """
    Use Case 3: User logs "ham and cheese sandwich" with estimates,
    then finds the actual nutrition label and wants to correct it.
    """

    @pytest.mark.asyncio
    async def test_update_food_entry(self, client, api_headers):
        today = date.today().isoformat()

        # Step 1: GPT logs sandwich with estimated macros (no ingredient)
        log = await client.post(
            "/api/v1/food",
            headers=api_headers,
            json={
                "date": today,
                "description": "Ham and Cheese Sandwich",
                "quantity": 1,
                "unit": "sandwich",
                "meal_label": "lunch",
                "protein_g": 20,  # GPT estimate
                "carbs_g": 30,
                "fat_g": 15,
                "sodium_mg": 800,
                "calories": 350,
            },
        )
        assert log.status_code == 201
        entry_id = log.json()["id"]

        # Step 2: User finds actual label - numbers are different!
        update = await client.patch(
            f"/api/v1/food/{entry_id}",
            headers=api_headers,
            json={
                "protein_g": 25,  # Actual from label
                "carbs_g": 35,
                "fat_g": 18,
                "sodium_mg": 950,
                "calories": 420,
            },
        )
        assert update.status_code == 200
        updated = update.json()

        # Verify the update worked
        assert updated["calories"] == 420
        assert updated["protein_g"] == 25
        assert updated["sodium_mg"] == 950

        # Step 3: Summary should reflect corrected values
        summary = await client.get(
            f"/api/v1/food/summary?date={today}",
            headers=api_headers,
        )
        assert summary.json()["total_calories"] == 420


class TestUseCase4_FavoriteProteinPowder:
    """
    Use Case 4: User has a favorite protein powder and wants it as default.
    Later logs a shake recipe using 2 scoops of their personal powder.
    """

    @pytest.mark.asyncio
    async def test_favorite_protein_powder_workflow(self, client, api_headers):
        # Step 1: User provides nutrition label for their protein powder
        label = await client.post(
            "/api/v1/nutrition-labels",
            headers=api_headers,
            json={
                "product_name": "Whey Protein Isolate",
                "brand": "Optimum Nutrition Gold Standard",
                "barcode": "748927028904",
                "serving_size": 31,
                "serving_unit": "g",
                "servings_per_container": 74,
                "calories": 120,
                "protein_g": 24,
                "carbs_g": 3,
                "fat_g": 1,
                "sodium_mg": 130,
            },
        )
        assert label.status_code == 201
        label_id = label.json()["id"]

        # Step 2: Convert to ingredient (this becomes their default)
        ingredient = await client.post(
            f"/api/v1/nutrition-labels/{label_id}/to-ingredient",
            headers=api_headers,
        )
        assert ingredient.status_code == 200
        powder_id = ingredient.json()["id"]

        # Verify the ingredient was created with correct name
        assert "Optimum Nutrition" in ingredient.json()["name"]

        # Step 3: User can search for it later
        search = await client.get(
            "/api/v1/ingredients/search?q=protein",
            headers=api_headers,
        )
        assert search.status_code == 200
        results = search.json()
        assert len(results) >= 1
        assert any("Optimum Nutrition" in r["name"] for r in results)

        # Step 4: Create a shake recipe with 2 scoops
        # First, add milk as another ingredient
        milk = await client.post(
            "/api/v1/ingredients",
            headers=api_headers,
            json={
                "name": "Whole Milk",
                "serving_size": 240,
                "serving_unit": "ml",
                "protein_g": 8,
                "carbs_g": 12,
                "fat_g": 8,
                "sodium_mg": 105,
                "calories": 150,
            },
        )
        milk_id = milk.json()["id"]

        recipe = await client.post(
            "/api/v1/recipes",
            headers=api_headers,
            json={
                "name": "My Protein Shake",
                "description": "Post-workout shake with 2 scoops",
                "ingredients": [
                    {"ingredient_id": powder_id, "quantity": 2, "unit": "serving"},  # 2 scoops
                    {"ingredient_id": milk_id, "quantity": 1, "unit": "serving"},
                ],
            },
        )
        assert recipe.status_code == 201
        recipe_data = recipe.json()

        # Verify recipe totals: 2 scoops (240cal) + milk (150cal) = 390cal
        assert recipe_data["total_calories"] == pytest.approx(390, rel=0.1)
        assert recipe_data["total_protein_g"] == pytest.approx(56, rel=0.1)  # 48 + 8

        # Step 5: Log the recipe
        today = date.today().isoformat()
        log = await client.post(
            f"/api/v1/recipes/{recipe_data['id']}/log?date={today}&servings=1",
            headers=api_headers,
        )
        assert log.status_code == 200

        # Verify it shows up in summary
        summary = await client.get(
            f"/api/v1/food/summary?date={today}",
            headers=api_headers,
        )
        assert summary.json()["total_protein_g"] == pytest.approx(56, rel=0.1)


class TestUseCase5_UpdateTargets:
    """
    Use Case 5: User periodically updates target macros based on GPT advice.
    """

    @pytest.mark.asyncio
    async def test_update_targets_over_time(self, client, api_headers):
        today = date.today().isoformat()

        # Step 1: Set initial targets
        targets = [
            {"name": "calories", "value": 2000, "unit": "kcal", "effective_from": today},
            {"name": "protein_g", "value": 150, "unit": "g", "effective_from": today},
            {"name": "carbs_g", "value": 200, "unit": "g", "effective_from": today},
            {"name": "fat_g", "value": 65, "unit": "g", "effective_from": today},
            {"name": "sodium_mg", "value": 2300, "unit": "mg", "effective_from": today},
        ]

        for target in targets:
            resp = await client.post(
                "/api/v1/targets",
                headers=api_headers,
                json=target,
            )
            assert resp.status_code == 201

        # Step 2: Get current targets
        current = await client.get("/api/v1/targets", headers=api_headers)
        assert current.status_code == 200
        assert len(current.json()) == 5

        # Step 3: Check dashboard shows progress against targets
        dashboard = await client.get(
            f"/api/v1/dashboard?date={today}",
            headers=api_headers,
        )
        assert dashboard.status_code == 200
        progress = dashboard.json()["target_progress"]
        assert len(progress) == 5

        # With no food logged, should be 0% progress
        for p in progress:
            assert p["current_value"] == 0
            assert p["percent_complete"] == 0

        # Step 4: GPT advises lowering calories - create new target
        next_week = (date.today() + timedelta(days=7)).isoformat()
        new_cal = await client.post(
            "/api/v1/targets",
            headers=api_headers,
            json={
                "name": "calories",
                "value": 1800,  # Reduced from 2000
                "unit": "kcal",
                "effective_from": next_week,
            },
        )
        assert new_cal.status_code == 201

        # Step 5: Current targets still show old value (not effective yet)
        current = await client.get("/api/v1/targets", headers=api_headers)
        cal_target = next(t for t in current.json() if t["name"] == "calories")
        assert cal_target["value"] == 2000  # Still the old value for today
