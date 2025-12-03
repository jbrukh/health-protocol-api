from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status

from app.database import get_db
from app.models.ingredient import IngredientCreate, IngredientResponse, IngredientUpdate


async def create_ingredient(data: IngredientCreate, db_path: str | None = None) -> IngredientResponse:
    """Create a new ingredient."""
    async with get_db(db_path) as db:
        try:
            cursor = await db.execute(
                """
                INSERT INTO ingredients (name, default_amount, default_unit, calories, protein_g, carbs_g, fats_g, sodium_mg)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data.name,
                    data.default_amount,
                    data.default_unit,
                    data.calories,
                    data.protein_g,
                    data.carbs_g,
                    data.fats_g,
                    data.sodium_mg,
                ),
            )
            await db.commit()
            ingredient_id = cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ingredient with name '{data.name}' already exists",
                )
            raise

        return await get_ingredient(ingredient_id, db_path)


async def get_ingredient(ingredient_id: int, db_path: str | None = None) -> IngredientResponse:
    """Get an ingredient by ID."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM ingredients WHERE id = ?",
            (ingredient_id,),
        )
        row = await cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ingredient with id {ingredient_id} not found",
            )

        return IngredientResponse(
            id=row["id"],
            name=row["name"],
            default_amount=row["default_amount"],
            default_unit=row["default_unit"],
            calories=row["calories"],
            protein_g=row["protein_g"],
            carbs_g=row["carbs_g"],
            fats_g=row["fats_g"],
            sodium_mg=row["sodium_mg"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )


async def list_ingredients(db_path: str | None = None) -> list[IngredientResponse]:
    """List all ingredients."""
    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT * FROM ingredients ORDER BY name")
        rows = await cursor.fetchall()

        return [
            IngredientResponse(
                id=row["id"],
                name=row["name"],
                default_amount=row["default_amount"],
                default_unit=row["default_unit"],
                calories=row["calories"],
                protein_g=row["protein_g"],
                carbs_g=row["carbs_g"],
                fats_g=row["fats_g"],
                sodium_mg=row["sodium_mg"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]


async def search_ingredients(query: str, db_path: str | None = None) -> list[IngredientResponse]:
    """Search ingredients by name (case-insensitive)."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM ingredients WHERE LOWER(name) LIKE ? ORDER BY name",
            (f"%{query.lower()}%",),
        )
        rows = await cursor.fetchall()

        return [
            IngredientResponse(
                id=row["id"],
                name=row["name"],
                default_amount=row["default_amount"],
                default_unit=row["default_unit"],
                calories=row["calories"],
                protein_g=row["protein_g"],
                carbs_g=row["carbs_g"],
                fats_g=row["fats_g"],
                sodium_mg=row["sodium_mg"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]


async def update_ingredient(
    ingredient_id: int, data: IngredientUpdate, db_path: str | None = None
) -> IngredientResponse:
    """Update an ingredient."""
    await get_ingredient(ingredient_id, db_path)

    async with get_db(db_path) as db:
        updates = []
        values = []
        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                updates.append(f"{field} = ?")
                values.append(value)

        if updates:
            values.append(ingredient_id)
            query = f"UPDATE ingredients SET {', '.join(updates)} WHERE id = ?"
            try:
                await db.execute(query, values)
                await db.commit()
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Ingredient with name '{data.name}' already exists",
                    )
                raise

    return await get_ingredient(ingredient_id, db_path)


async def delete_ingredient(ingredient_id: int, db_path: str | None = None) -> None:
    """Delete an ingredient."""
    await get_ingredient(ingredient_id, db_path)

    async with get_db(db_path) as db:
        await db.execute("DELETE FROM ingredients WHERE id = ?", (ingredient_id,))
        await db.commit()
