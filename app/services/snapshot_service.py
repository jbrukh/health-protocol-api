from datetime import date, datetime, timedelta

from app.database import get_db
from app.models.macro import MacroTotals


async def compute_snapshot(snapshot_date: date, db_path: str | None = None) -> MacroTotals:
    """Compute macro totals for a date from foods table."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            """
            SELECT
                COALESCE(SUM(calories), 0) as calories,
                COALESCE(SUM(protein_g), 0) as protein_g,
                COALESCE(SUM(carbs_g), 0) as carbs_g,
                COALESCE(SUM(fats_g), 0) as fats_g,
                COALESCE(SUM(sodium_mg), 0) as sodium_mg
            FROM foods
            WHERE date = ?
            """,
            (snapshot_date.isoformat(),),
        )
        row = await cursor.fetchone()

        return MacroTotals(
            calories=row["calories"],
            protein_g=round(row["protein_g"], 1),
            carbs_g=round(row["carbs_g"], 1),
            fats_g=round(row["fats_g"], 1),
            sodium_mg=row["sodium_mg"],
        )


async def get_or_create_snapshot(snapshot_date: date, db_path: str | None = None) -> MacroTotals:
    """Get existing snapshot or compute and store a new one."""
    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT * FROM daily_snapshots WHERE date = ?",
            (snapshot_date.isoformat(),),
        )
        row = await cursor.fetchone()

        if row:
            return MacroTotals(
                calories=row["calories"],
                protein_g=row["protein_g"],
                carbs_g=row["carbs_g"],
                fats_g=row["fats_g"],
                sodium_mg=row["sodium_mg"],
            )

        totals = await compute_snapshot(snapshot_date, db_path)

        await db.execute(
            """
            INSERT INTO daily_snapshots (date, calories, protein_g, carbs_g, fats_g, sodium_mg)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot_date.isoformat(),
                totals.calories,
                totals.protein_g,
                totals.carbs_g,
                totals.fats_g,
                totals.sodium_mg,
            ),
        )
        await db.commit()

        return totals


async def generate_missing_snapshots(
    start_date: date, end_date: date, db_path: str | None = None
) -> dict[date, MacroTotals]:
    """Generate snapshots for all dates in range that don't have one."""
    snapshots = {}
    current = start_date
    while current <= end_date:
        snapshots[current] = await get_or_create_snapshot(current, db_path)
        current = current + timedelta(days=1)
    return snapshots


async def invalidate_snapshot(snapshot_date: date, db_path: str | None = None) -> None:
    """Delete a cached snapshot so it will be recomputed on next access."""
    async with get_db(db_path) as db:
        await db.execute(
            "DELETE FROM daily_snapshots WHERE date = ?",
            (snapshot_date.isoformat(),),
        )
        await db.commit()
