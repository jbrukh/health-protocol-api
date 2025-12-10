from datetime import datetime

from fastapi import HTTPException, status

from app.database import get_db
from app.models.recipe import (
    RecipeCreate,
    RecipeResponse,
    RecipeListResponse,
    RecipeUpdate,
    RecipeItemCreate,
    RecipeItemResponse,
    RecipeItemUpdate,
    RecipeTotals,
)


async def compute_recipe_totals(items: list[RecipeItemResponse]) -> RecipeTotals:
    """Compute total macros from recipe items."""
    return RecipeTotals(
        calories=sum(item.calories for item in items),
        protein_g=round(sum(item.protein_g for item in items), 1),
        carbs_g=round(sum(item.carbs_g for item in items), 1),
        fats_g=round(sum(item.fats_g for item in items), 1),
        sodium_mg=sum(item.sodium_mg for item in items),
    )


async def get_recipe_items(recipe_id: int, db_path: str | None = None) -> list[RecipeItemResponse]:
    """Get all items for a recipe with computed macros."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            """
            SELECT ri.id, ri.ingredient_id, ri.amount, ri.unit,
                   i.name as ingredient_name, i.default_amount,
                   i.calories, i.protein_g, i.carbs_g, i.fats_g, i.sodium_mg
            FROM recipe_items ri
            JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE ri.recipe_id = ?
            """,
            (recipe_id,),
        )
        rows = await cursor.fetchall()

        items = []
        for row in rows:
            scale = row["amount"] / row["default_amount"] if row["default_amount"] else 1
            items.append(
                RecipeItemResponse(
                    id=row["id"],
                    ingredient_id=row["ingredient_id"],
                    ingredient_name=row["ingredient_name"],
                    amount=row["amount"],
                    unit=row["unit"],
                    calories=round(row["calories"] * scale),
                    protein_g=round(row["protein_g"] * scale, 1),
                    carbs_g=round(row["carbs_g"] * scale, 1),
                    fats_g=round(row["fats_g"] * scale, 1),
                    sodium_mg=round(row["sodium_mg"] * scale),
                )
            )
        return items


async def create_recipe(data: RecipeCreate, db_path: str | None = None) -> RecipeResponse:
    """Create a new recipe with items."""
    async with get_db(db_path) as db:
        try:
            cursor = await db.execute(
                "INSERT INTO recipes (name) VALUES (?)",
                (data.name,),
            )
            await db.commit()
            recipe_id = cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Recipe with name '{data.name}' already exists",
                )
            raise

        for item in data.items:
            cursor = await db.execute(
                "SELECT id FROM ingredients WHERE id = ?",
                (item.ingredient_id,),
            )
            if not await cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ingredient with id {item.ingredient_id} not found",
                )

            await db.execute(
                """
                INSERT INTO recipe_items (recipe_id, ingredient_id, amount, unit)
                VALUES (?, ?, ?, ?)
                """,
                (recipe_id, item.ingredient_id, item.amount, item.unit),
            )
        await db.commit()

    return await get_recipe(recipe_id, db_path)


async def get_recipe(recipe_id: int, db_path: str | None = None) -> RecipeResponse:
    """Get a recipe by ID with items and totals."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM recipes WHERE id = ?",
            (recipe_id,),
        )
        row = await cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe with id {recipe_id} not found",
            )

        items = await get_recipe_items(recipe_id, db_path)
        totals = await compute_recipe_totals(items)

        return RecipeResponse(
            id=row["id"],
            name=row["name"],
            items=items,
            totals=totals,
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


async def list_recipes(db_path: str | None = None) -> list[RecipeListResponse]:
    """List all recipes with computed totals using a single query."""
    async with get_db(db_path) as db:
        # Fetch all recipes with their items in a single JOIN query
        cursor = await db.execute(
            """
            SELECT r.id, r.name, r.created_at, r.updated_at,
                   ri.id as item_id, ri.ingredient_id, ri.amount, ri.unit,
                   i.name as ingredient_name, i.default_amount,
                   i.calories, i.protein_g, i.carbs_g, i.fats_g, i.sodium_mg
            FROM recipes r
            LEFT JOIN recipe_items ri ON r.id = ri.recipe_id
            LEFT JOIN ingredients i ON ri.ingredient_id = i.id
            ORDER BY r.name, ri.id
            """
        )
        rows = await cursor.fetchall()

        # Group items by recipe
        recipes_dict: dict[int, dict] = {}
        for row in rows:
            recipe_id = row["id"]
            if recipe_id not in recipes_dict:
                recipes_dict[recipe_id] = {
                    "id": recipe_id,
                    "name": row["name"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "items": [],
                }

            # Only add item if it exists (LEFT JOIN may return NULL)
            if row["item_id"] is not None:
                scale = row["amount"] / row["default_amount"] if row["default_amount"] else 1
                recipes_dict[recipe_id]["items"].append(
                    RecipeItemResponse(
                        id=row["item_id"],
                        ingredient_id=row["ingredient_id"],
                        ingredient_name=row["ingredient_name"],
                        amount=row["amount"],
                        unit=row["unit"],
                        calories=round(row["calories"] * scale),
                        protein_g=round(row["protein_g"] * scale, 1),
                        carbs_g=round(row["carbs_g"] * scale, 1),
                        fats_g=round(row["fats_g"] * scale, 1),
                        sodium_mg=round(row["sodium_mg"] * scale),
                    )
                )

        # Convert to response objects with computed totals
        recipes = []
        for recipe_data in recipes_dict.values():
            items = recipe_data["items"]
            totals = RecipeTotals(
                calories=sum(item.calories for item in items),
                protein_g=round(sum(item.protein_g for item in items), 1),
                carbs_g=round(sum(item.carbs_g for item in items), 1),
                fats_g=round(sum(item.fats_g for item in items), 1),
                sodium_mg=sum(item.sodium_mg for item in items),
            )
            recipes.append(
                RecipeListResponse(
                    id=recipe_data["id"],
                    name=recipe_data["name"],
                    totals=totals,
                    created_at=datetime.fromisoformat(recipe_data["created_at"]),
                    updated_at=datetime.fromisoformat(recipe_data["updated_at"]),
                )
            )

        return recipes


async def update_recipe(recipe_id: int, data: RecipeUpdate, db_path: str | None = None) -> RecipeResponse:
    """Update a recipe's name."""
    await get_recipe(recipe_id, db_path)

    async with get_db(db_path) as db:
        if data.name is not None:
            try:
                await db.execute(
                    "UPDATE recipes SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (data.name, recipe_id),
                )
                await db.commit()
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Recipe with name '{data.name}' already exists",
                    )
                raise

    return await get_recipe(recipe_id, db_path)


async def add_recipe_item(recipe_id: int, data: RecipeItemCreate, db_path: str | None = None) -> RecipeResponse:
    """Add an item to a recipe."""
    await get_recipe(recipe_id, db_path)

    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT id FROM ingredients WHERE id = ?",
            (data.ingredient_id,),
        )
        if not await cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ingredient with id {data.ingredient_id} not found",
            )

        await db.execute(
            """
            INSERT INTO recipe_items (recipe_id, ingredient_id, amount, unit)
            VALUES (?, ?, ?, ?)
            """,
            (recipe_id, data.ingredient_id, data.amount, data.unit),
        )
        await db.execute(
            "UPDATE recipes SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (recipe_id,),
        )
        await db.commit()

    return await get_recipe(recipe_id, db_path)


async def update_recipe_item(
    recipe_id: int, item_id: int, data: RecipeItemUpdate, db_path: str | None = None
) -> RecipeResponse:
    """Update an item in a recipe."""
    await get_recipe(recipe_id, db_path)

    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT id FROM recipe_items WHERE id = ? AND recipe_id = ?",
            (item_id, recipe_id),
        )
        if not await cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe item with id {item_id} not found in recipe {recipe_id}",
            )

        updates = []
        values = []
        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                updates.append(f"{field} = ?")
                values.append(value)

        if updates:
            values.extend([item_id, recipe_id])
            query = f"UPDATE recipe_items SET {', '.join(updates)} WHERE id = ? AND recipe_id = ?"
            await db.execute(query, values)
            await db.execute(
                "UPDATE recipes SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (recipe_id,),
            )
            await db.commit()

    return await get_recipe(recipe_id, db_path)


async def delete_recipe_item(recipe_id: int, item_id: int, db_path: str | None = None) -> RecipeResponse:
    """Delete an item from a recipe."""
    await get_recipe(recipe_id, db_path)

    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT id FROM recipe_items WHERE id = ? AND recipe_id = ?",
            (item_id, recipe_id),
        )
        if not await cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe item with id {item_id} not found in recipe {recipe_id}",
            )

        await db.execute(
            "DELETE FROM recipe_items WHERE id = ? AND recipe_id = ?",
            (item_id, recipe_id),
        )
        await db.execute(
            "UPDATE recipes SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (recipe_id,),
        )
        await db.commit()

    return await get_recipe(recipe_id, db_path)


async def delete_recipe(recipe_id: int, db_path: str | None = None) -> None:
    """Delete a recipe (cascades to items)."""
    await get_recipe(recipe_id, db_path)

    async with get_db(db_path) as db:
        await db.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        await db.commit()
