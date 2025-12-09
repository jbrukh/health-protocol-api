from datetime import date, datetime
from typing import Optional

from fastapi import HTTPException, status

from app.database import get_db
from app.models.food import FoodCreate, FoodResponse, FoodFromRecipe, FoodUpdate
from app.services.recipe_service import get_recipe
from app.services.snapshot_service import invalidate_snapshot


async def create_food(data: FoodCreate, db_path: str | None = None) -> FoodResponse:
    """Create a food entry directly."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            """
            INSERT INTO foods (date, marker, name, amount, unit, calories, protein_g, carbs_g, fats_g, sodium_mg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.date.isoformat(),
                data.marker,
                data.name,
                data.amount,
                data.unit,
                data.calories,
                data.protein_g,
                data.carbs_g,
                data.fats_g,
                data.sodium_mg,
            ),
        )
        await db.commit()
        food_id = cursor.lastrowid

    # Invalidate cached snapshot for this date
    await invalidate_snapshot(data.date, db_path)

    return await get_food(food_id, db_path)


async def create_foods_from_recipe(data: FoodFromRecipe, db_path: str | None = None) -> list[FoodResponse]:
    """Create food entries from a recipe (expands to individual entries)."""
    recipe = await get_recipe(data.recipe_id, db_path)

    created_foods = []
    async with get_db(db_path) as db:
        for item in recipe.items:
            scaled_calories = round(item.calories * data.scale)
            scaled_protein = round(item.protein_g * data.scale, 1)
            scaled_carbs = round(item.carbs_g * data.scale, 1)
            scaled_fats = round(item.fats_g * data.scale, 1)
            scaled_sodium = round(item.sodium_mg * data.scale)
            scaled_amount = round(item.amount * data.scale, 2)

            cursor = await db.execute(
                """
                INSERT INTO foods (date, marker, name, amount, unit, calories, protein_g, carbs_g, fats_g, sodium_mg, ingredient_id, recipe_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data.date.isoformat(),
                    data.marker,
                    item.ingredient_name,
                    scaled_amount,
                    item.unit,
                    scaled_calories,
                    scaled_protein,
                    scaled_carbs,
                    scaled_fats,
                    scaled_sodium,
                    item.ingredient_id,
                    data.recipe_id,
                ),
            )
            created_foods.append(cursor.lastrowid)
        await db.commit()

    # Invalidate cached snapshot for this date
    await invalidate_snapshot(data.date, db_path)

    return [await get_food(food_id, db_path) for food_id in created_foods]


async def get_food(food_id: int, db_path: str | None = None) -> FoodResponse:
    """Get a food entry by ID."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM foods WHERE id = ?",
            (food_id,),
        )
        row = await cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Food entry with id {food_id} not found",
            )

        return FoodResponse(
            id=row["id"],
            date=date.fromisoformat(row["date"]),
            marker=row["marker"],
            name=row["name"],
            amount=row["amount"],
            unit=row["unit"],
            calories=row["calories"],
            protein_g=row["protein_g"],
            carbs_g=row["carbs_g"],
            fats_g=row["fats_g"],
            sodium_mg=row["sodium_mg"],
            ingredient_id=row["ingredient_id"],
            recipe_id=row["recipe_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )


async def get_foods(
    food_date: date, marker: Optional[str] = None, db_path: str | None = None
) -> list[FoodResponse]:
    """Get food entries for a date, optionally filtered by marker."""
    async with get_db(db_path) as db:
        if marker:
            cursor = await db.execute(
                "SELECT * FROM foods WHERE date = ? AND marker = ? ORDER BY created_at",
                (food_date.isoformat(), marker),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM foods WHERE date = ? ORDER BY created_at",
                (food_date.isoformat(),),
            )
        rows = await cursor.fetchall()

        return [
            FoodResponse(
                id=row["id"],
                date=date.fromisoformat(row["date"]),
                marker=row["marker"],
                name=row["name"],
                amount=row["amount"],
                unit=row["unit"],
                calories=row["calories"],
                protein_g=row["protein_g"],
                carbs_g=row["carbs_g"],
                fats_g=row["fats_g"],
                sodium_mg=row["sodium_mg"],
                ingredient_id=row["ingredient_id"],
                recipe_id=row["recipe_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]


async def update_food(food_id: int, data: FoodUpdate, db_path: str | None = None) -> FoodResponse:
    """Update a food entry."""
    existing_food = await get_food(food_id, db_path)

    async with get_db(db_path) as db:
        updates = []
        values = []
        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                updates.append(f"{field} = ?")
                values.append(value)

        if updates:
            values.append(food_id)
            query = f"UPDATE foods SET {', '.join(updates)} WHERE id = ?"
            await db.execute(query, values)
            await db.commit()

    # Invalidate cached snapshot for this date
    await invalidate_snapshot(existing_food.date, db_path)

    return await get_food(food_id, db_path)


async def delete_food(food_id: int, db_path: str | None = None) -> None:
    """Delete a food entry."""
    existing_food = await get_food(food_id, db_path)

    async with get_db(db_path) as db:
        await db.execute("DELETE FROM foods WHERE id = ?", (food_id,))
        await db.commit()

    # Invalidate cached snapshot for this date
    await invalidate_snapshot(existing_food.date, db_path)


async def delete_foods_by_marker(food_date: date, marker: str, db_path: str | None = None) -> int:
    """Delete all food entries with a specific marker on a date."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "DELETE FROM foods WHERE date = ? AND marker = ?",
            (food_date.isoformat(), marker),
        )
        await db.commit()
        count = cursor.rowcount

    # Invalidate cached snapshot for this date
    if count > 0:
        await invalidate_snapshot(food_date, db_path)

    return count


async def clear_foods_by_date(food_date: date, db_path: str | None = None) -> int:
    """Clear all food entries for a date."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "DELETE FROM foods WHERE date = ?",
            (food_date.isoformat(),),
        )
        await db.commit()
        count = cursor.rowcount

    # Invalidate cached snapshot for this date
    if count > 0:
        await invalidate_snapshot(food_date, db_path)

    return count
