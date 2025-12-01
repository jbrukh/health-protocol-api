"""Nutrition calculation services."""

from typing import Dict, List
from app.models import Ingredient, RecipeIngredient
from app.utils.units import calculate_nutrition_multiplier


def calculate_entry_nutrition(
    ingredient: Ingredient,
    quantity: float,
    unit: str,
) -> Dict[str, float]:
    """Calculate nutrition values for a food entry based on ingredient and quantity."""
    multiplier = calculate_nutrition_multiplier(
        consumed_quantity=quantity,
        consumed_unit=unit,
        serving_size=ingredient.serving_size,
        serving_unit=ingredient.serving_unit,
    )

    return {
        "protein_g": round(ingredient.protein_g * multiplier, 2),
        "carbs_g": round(ingredient.carbs_g * multiplier, 2),
        "fat_g": round(ingredient.fat_g * multiplier, 2),
        "sodium_mg": round(ingredient.sodium_mg * multiplier, 2),
        "calories": round(ingredient.calories * multiplier, 2),
    }


def calculate_recipe_nutrition(
    recipe_ingredients: List[RecipeIngredient],
) -> Dict[str, float]:
    """Calculate total nutrition values for a recipe."""
    totals = {
        "protein_g": 0.0,
        "carbs_g": 0.0,
        "fat_g": 0.0,
        "sodium_mg": 0.0,
        "calories": 0.0,
    }

    for ri in recipe_ingredients:
        if ri.ingredient:
            nutrition = calculate_entry_nutrition(
                ri.ingredient, ri.quantity, ri.unit
            )
            for key in totals:
                totals[key] += nutrition[key]

    # Round final totals
    return {k: round(v, 2) for k, v in totals.items()}
