"""Unit tests for nutrition calculation services."""

import pytest
from unittest.mock import MagicMock
from app.services.nutrition import calculate_entry_nutrition, calculate_recipe_nutrition


class TestCalculateEntryNutrition:
    def test_basic_calculation(self):
        """Test nutrition calculation with same units."""
        ingredient = MagicMock()
        ingredient.serving_size = 30
        ingredient.serving_unit = "g"
        ingredient.protein_g = 10
        ingredient.carbs_g = 20
        ingredient.fat_g = 5
        ingredient.sodium_mg = 100
        ingredient.calories = 150

        result = calculate_entry_nutrition(ingredient, 60, "g")

        # 60g / 30g = 2x multiplier
        assert result["protein_g"] == 20
        assert result["carbs_g"] == 40
        assert result["fat_g"] == 10
        assert result["sodium_mg"] == 200
        assert result["calories"] == 300

    def test_half_serving(self):
        """Test calculation with half serving."""
        ingredient = MagicMock()
        ingredient.serving_size = 100
        ingredient.serving_unit = "g"
        ingredient.protein_g = 20
        ingredient.carbs_g = 30
        ingredient.fat_g = 10
        ingredient.sodium_mg = 500
        ingredient.calories = 250

        result = calculate_entry_nutrition(ingredient, 50, "g")

        assert result["protein_g"] == 10
        assert result["carbs_g"] == 15
        assert result["fat_g"] == 5
        assert result["sodium_mg"] == 250
        assert result["calories"] == 125

    def test_serving_unit(self):
        """Test calculation using 'serving' as unit."""
        ingredient = MagicMock()
        ingredient.serving_size = 30
        ingredient.serving_unit = "g"
        ingredient.protein_g = 25
        ingredient.carbs_g = 5
        ingredient.fat_g = 2
        ingredient.sodium_mg = 150
        ingredient.calories = 130

        result = calculate_entry_nutrition(ingredient, 2, "serving")

        assert result["protein_g"] == 50
        assert result["carbs_g"] == 10
        assert result["fat_g"] == 4
        assert result["sodium_mg"] == 300
        assert result["calories"] == 260

    def test_rounding(self):
        """Test that results are rounded to 2 decimal places."""
        ingredient = MagicMock()
        ingredient.serving_size = 30
        ingredient.serving_unit = "g"
        ingredient.protein_g = 10
        ingredient.carbs_g = 10
        ingredient.fat_g = 10
        ingredient.sodium_mg = 100
        ingredient.calories = 100

        # 1/3 serving should give rounded results
        result = calculate_entry_nutrition(ingredient, 10, "g")

        assert result["protein_g"] == 3.33
        assert result["carbs_g"] == 3.33
        assert result["fat_g"] == 3.33
        assert result["sodium_mg"] == 33.33
        assert result["calories"] == 33.33


class TestCalculateRecipeNutrition:
    def test_empty_recipe(self):
        """Test empty recipe returns zeros."""
        result = calculate_recipe_nutrition([])

        assert result["protein_g"] == 0
        assert result["carbs_g"] == 0
        assert result["fat_g"] == 0
        assert result["sodium_mg"] == 0
        assert result["calories"] == 0

    def test_single_ingredient(self):
        """Test recipe with single ingredient."""
        ingredient = MagicMock()
        ingredient.serving_size = 30
        ingredient.serving_unit = "g"
        ingredient.protein_g = 10
        ingredient.carbs_g = 20
        ingredient.fat_g = 5
        ingredient.sodium_mg = 100
        ingredient.calories = 150

        recipe_ingredient = MagicMock()
        recipe_ingredient.ingredient = ingredient
        recipe_ingredient.quantity = 30
        recipe_ingredient.unit = "g"

        result = calculate_recipe_nutrition([recipe_ingredient])

        assert result["protein_g"] == 10
        assert result["carbs_g"] == 20
        assert result["fat_g"] == 5
        assert result["sodium_mg"] == 100
        assert result["calories"] == 150

    def test_multiple_ingredients(self):
        """Test recipe with multiple ingredients."""
        # First ingredient
        ing1 = MagicMock()
        ing1.serving_size = 30
        ing1.serving_unit = "g"
        ing1.protein_g = 10
        ing1.carbs_g = 5
        ing1.fat_g = 2
        ing1.sodium_mg = 50
        ing1.calories = 80

        ri1 = MagicMock()
        ri1.ingredient = ing1
        ri1.quantity = 30
        ri1.unit = "g"

        # Second ingredient
        ing2 = MagicMock()
        ing2.serving_size = 100
        ing2.serving_unit = "ml"
        ing2.protein_g = 8
        ing2.carbs_g = 12
        ing2.fat_g = 5
        ing2.sodium_mg = 120
        ing2.calories = 150

        ri2 = MagicMock()
        ri2.ingredient = ing2
        ri2.quantity = 200
        ri2.unit = "ml"

        result = calculate_recipe_nutrition([ri1, ri2])

        # ri1: 1x multiplier, ri2: 2x multiplier
        assert result["protein_g"] == 10 + 16  # 26
        assert result["carbs_g"] == 5 + 24  # 29
        assert result["fat_g"] == 2 + 10  # 12
        assert result["sodium_mg"] == 50 + 240  # 290
        assert result["calories"] == 80 + 300  # 380

    def test_null_ingredient_skipped(self):
        """Test that recipe ingredients with null ingredient are skipped."""
        ri = MagicMock()
        ri.ingredient = None
        ri.quantity = 30
        ri.unit = "g"

        result = calculate_recipe_nutrition([ri])

        assert result["protein_g"] == 0
        assert result["calories"] == 0
