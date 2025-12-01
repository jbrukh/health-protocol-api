"""Unit conversion utilities for nutrition calculations."""

from typing import Optional

# Weight conversions to grams
WEIGHT_TO_GRAMS = {
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,
    "oz": 28.3495,
    "ounce": 28.3495,
    "ounces": 28.3495,
    "lb": 453.592,
    "lbs": 453.592,
    "pound": 453.592,
    "pounds": 453.592,
    "kg": 1000.0,
    "kilogram": 1000.0,
    "kilograms": 1000.0,
}

# Volume conversions to milliliters
VOLUME_TO_ML = {
    "ml": 1.0,
    "milliliter": 1.0,
    "milliliters": 1.0,
    "l": 1000.0,
    "liter": 1000.0,
    "liters": 1000.0,
    "tbsp": 14.787,
    "tablespoon": 14.787,
    "tablespoons": 14.787,
    "tsp": 4.929,
    "teaspoon": 4.929,
    "teaspoons": 4.929,
    "cup": 236.588,
    "cups": 236.588,
    "fl oz": 29.5735,
    "fluid ounce": 29.5735,
    "fluid ounces": 29.5735,
}


def normalize_unit(unit: str) -> str:
    """Normalize unit string to lowercase without extra spaces."""
    return unit.lower().strip()


def convert_to_grams(quantity: float, unit: str) -> Optional[float]:
    """Convert a weight quantity to grams. Returns None if not a weight unit."""
    normalized = normalize_unit(unit)
    if normalized in WEIGHT_TO_GRAMS:
        return quantity * WEIGHT_TO_GRAMS[normalized]
    return None


def convert_to_ml(quantity: float, unit: str) -> Optional[float]:
    """Convert a volume quantity to milliliters. Returns None if not a volume unit."""
    normalized = normalize_unit(unit)
    if normalized in VOLUME_TO_ML:
        return quantity * VOLUME_TO_ML[normalized]
    return None


def is_weight_unit(unit: str) -> bool:
    """Check if the unit is a weight unit."""
    return normalize_unit(unit) in WEIGHT_TO_GRAMS


def is_volume_unit(unit: str) -> bool:
    """Check if the unit is a volume unit."""
    return normalize_unit(unit) in VOLUME_TO_ML


def calculate_nutrition_multiplier(
    consumed_quantity: float,
    consumed_unit: str,
    serving_size: float,
    serving_unit: str,
) -> float:
    """
    Calculate the multiplier to apply to nutrition values based on consumed vs serving size.

    For example, if a serving is 30g and you consumed 60g, the multiplier is 2.0.
    If units are 'serving' or 'servings', the quantity itself is the multiplier.
    """
    consumed_normalized = normalize_unit(consumed_unit)
    serving_normalized = normalize_unit(serving_unit)

    # Handle 'serving' as a special unit
    if consumed_normalized in ("serving", "servings"):
        return consumed_quantity

    # If both are weight units, convert to grams and compare
    if is_weight_unit(consumed_unit) and is_weight_unit(serving_unit):
        consumed_grams = convert_to_grams(consumed_quantity, consumed_unit)
        serving_grams = convert_to_grams(serving_size, serving_unit)
        if consumed_grams and serving_grams:
            return consumed_grams / serving_grams

    # If both are volume units, convert to ml and compare
    if is_volume_unit(consumed_unit) and is_volume_unit(serving_unit):
        consumed_ml = convert_to_ml(consumed_quantity, consumed_unit)
        serving_ml = convert_to_ml(serving_size, serving_unit)
        if consumed_ml and serving_ml:
            return consumed_ml / serving_ml

    # If same unit, just divide quantities
    if consumed_normalized == serving_normalized:
        return consumed_quantity / serving_size

    # Default: assume 1:1 ratio (user should ensure units match)
    return consumed_quantity / serving_size
