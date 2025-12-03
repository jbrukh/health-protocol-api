from datetime import date, datetime
from typing import Optional

from app.database import get_db
from app.models.profile import ProfileResponse, ProfileTargets, ProfileUpdate


def compute_age(birthdate: Optional[date]) -> Optional[int]:
    """Compute age from birthdate."""
    if birthdate is None:
        return None
    today = date.today()
    age = today.year - birthdate.year
    if (today.month, today.day) < (birthdate.month, birthdate.day):
        age -= 1
    return age


async def get_profile(db_path: str | None = None) -> ProfileResponse:
    """Get profile or create default if none exists."""
    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT * FROM user_profile WHERE id = 1")
        row = await cursor.fetchone()

        if row is None:
            await db.execute(
                """
                INSERT INTO user_profile (id) VALUES (1)
                """
            )
            await db.commit()
            cursor = await db.execute("SELECT * FROM user_profile WHERE id = 1")
            row = await cursor.fetchone()

        birthdate = None
        if row["birthdate"]:
            birthdate = date.fromisoformat(row["birthdate"])

        return ProfileResponse(
            birthdate=birthdate,
            age=compute_age(birthdate),
            height_inches=row["height_inches"],
            targets=ProfileTargets(
                calories_min=row["calories_min"],
                calories_max=row["calories_max"],
                protein_min_g=row["protein_min_g"],
                protein_max_g=row["protein_max_g"],
                carbs_min_g=row["carbs_min_g"],
                carbs_max_g=row["carbs_max_g"],
                fats_min_g=row["fats_min_g"],
                fats_max_g=row["fats_max_g"],
                sodium_max_mg=row["sodium_max_mg"],
            ),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
        )


async def update_profile(data: ProfileUpdate, db_path: str | None = None) -> ProfileResponse:
    """Update profile (upsert)."""
    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT id FROM user_profile WHERE id = 1")
        exists = await cursor.fetchone()

        if not exists:
            await db.execute("INSERT INTO user_profile (id) VALUES (1)")
            await db.commit()

        updates = []
        values = []
        for field, value in data.model_dump(exclude_unset=True).items():
            if value is not None:
                updates.append(f"{field} = ?")
                if isinstance(value, date):
                    values.append(value.isoformat())
                else:
                    values.append(value)

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            query = f"UPDATE user_profile SET {', '.join(updates)} WHERE id = 1"
            await db.execute(query, values)
            await db.commit()

    return await get_profile(db_path)
