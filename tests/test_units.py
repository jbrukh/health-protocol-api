"""Unit tests for unit conversion utilities."""

import pytest
from app.utils.units import (
    normalize_unit,
    convert_to_grams,
    convert_to_ml,
    is_weight_unit,
    is_volume_unit,
    calculate_nutrition_multiplier,
)


class TestNormalizeUnit:
    def test_lowercase(self):
        assert normalize_unit("G") == "g"
        assert normalize_unit("OZ") == "oz"

    def test_strips_whitespace(self):
        assert normalize_unit("  g  ") == "g"
        assert normalize_unit("\toz\n") == "oz"


class TestConvertToGrams:
    def test_grams(self):
        assert convert_to_grams(100, "g") == 100
        assert convert_to_grams(100, "grams") == 100

    def test_ounces(self):
        result = convert_to_grams(1, "oz")
        assert result == pytest.approx(28.3495, rel=1e-3)

    def test_pounds(self):
        result = convert_to_grams(1, "lb")
        assert result == pytest.approx(453.592, rel=1e-3)

    def test_kilograms(self):
        result = convert_to_grams(1, "kg")
        assert result == 1000

    def test_invalid_unit_returns_none(self):
        assert convert_to_grams(100, "ml") is None
        assert convert_to_grams(100, "cup") is None


class TestConvertToMl:
    def test_milliliters(self):
        assert convert_to_ml(100, "ml") == 100
        assert convert_to_ml(100, "milliliters") == 100

    def test_tablespoon(self):
        result = convert_to_ml(1, "tbsp")
        assert result == pytest.approx(14.787, rel=1e-3)

    def test_teaspoon(self):
        result = convert_to_ml(1, "tsp")
        assert result == pytest.approx(4.929, rel=1e-3)

    def test_cup(self):
        result = convert_to_ml(1, "cup")
        assert result == pytest.approx(236.588, rel=1e-3)

    def test_liter(self):
        assert convert_to_ml(1, "l") == 1000

    def test_invalid_unit_returns_none(self):
        assert convert_to_ml(100, "g") is None
        assert convert_to_ml(100, "oz") is None


class TestIsWeightUnit:
    def test_weight_units(self):
        assert is_weight_unit("g") is True
        assert is_weight_unit("oz") is True
        assert is_weight_unit("lb") is True
        assert is_weight_unit("kg") is True

    def test_non_weight_units(self):
        assert is_weight_unit("ml") is False
        assert is_weight_unit("cup") is False
        assert is_weight_unit("serving") is False


class TestIsVolumeUnit:
    def test_volume_units(self):
        assert is_volume_unit("ml") is True
        assert is_volume_unit("tbsp") is True
        assert is_volume_unit("cup") is True
        assert is_volume_unit("l") is True

    def test_non_volume_units(self):
        assert is_volume_unit("g") is False
        assert is_volume_unit("oz") is False
        assert is_volume_unit("serving") is False


class TestCalculateNutritionMultiplier:
    def test_same_units(self):
        # 60g consumed / 30g serving = 2x multiplier
        result = calculate_nutrition_multiplier(60, "g", 30, "g")
        assert result == 2.0

    def test_serving_unit(self):
        # 2 servings = 2x multiplier
        result = calculate_nutrition_multiplier(2, "serving", 30, "g")
        assert result == 2.0

        result = calculate_nutrition_multiplier(0.5, "servings", 100, "g")
        assert result == 0.5

    def test_weight_conversion(self):
        # 1 oz consumed / 28.3495g serving ≈ 1x multiplier
        result = calculate_nutrition_multiplier(1, "oz", 28.3495, "g")
        assert result == pytest.approx(1.0, rel=1e-2)

    def test_volume_conversion(self):
        # 2 tbsp consumed / 1 tbsp serving = 2x multiplier
        result = calculate_nutrition_multiplier(2, "tbsp", 1, "tbsp")
        assert result == 2.0

        # 1 cup / 236.588 ml = 1x multiplier
        result = calculate_nutrition_multiplier(1, "cup", 236.588, "ml")
        assert result == pytest.approx(1.0, rel=1e-2)

    def test_half_serving(self):
        result = calculate_nutrition_multiplier(15, "g", 30, "g")
        assert result == 0.5
