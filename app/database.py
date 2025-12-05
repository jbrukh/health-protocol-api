import aiosqlite
from contextlib import asynccontextmanager
from pathlib import Path

from app.config import settings

SCHEMA = """
-- User profile (single row)
CREATE TABLE IF NOT EXISTS user_profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    birthdate DATE,
    height_inches REAL,
    calories_min INTEGER NOT NULL DEFAULT 1800,
    calories_max INTEGER NOT NULL DEFAULT 2200,
    protein_min_g INTEGER NOT NULL DEFAULT 150,
    protein_max_g INTEGER NOT NULL DEFAULT 180,
    carbs_min_g INTEGER NOT NULL DEFAULT 150,
    carbs_max_g INTEGER NOT NULL DEFAULT 200,
    fats_min_g INTEGER NOT NULL DEFAULT 50,
    fats_max_g INTEGER NOT NULL DEFAULT 70,
    sodium_max_mg INTEGER NOT NULL DEFAULT 2300,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ingredients
CREATE TABLE IF NOT EXISTS ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    default_amount REAL NOT NULL,
    default_unit TEXT NOT NULL,
    calories INTEGER NOT NULL,
    protein_g REAL NOT NULL,
    carbs_g REAL NOT NULL,
    fats_g REAL NOT NULL,
    sodium_mg INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recipes
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recipe items (junction table)
CREATE TABLE IF NOT EXISTS recipe_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id),
    amount REAL NOT NULL,
    unit TEXT NOT NULL
);

-- Foods (logged entries)
CREATE TABLE IF NOT EXISTS foods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    marker TEXT NOT NULL,
    name TEXT NOT NULL,
    amount REAL NOT NULL,
    unit TEXT NOT NULL,
    calories INTEGER NOT NULL,
    protein_g REAL NOT NULL,
    carbs_g REAL NOT NULL,
    fats_g REAL NOT NULL,
    sodium_mg INTEGER NOT NULL DEFAULT 0,
    ingredient_id INTEGER REFERENCES ingredients(id),
    recipe_id INTEGER REFERENCES recipes(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_foods_date ON foods(date);
CREATE INDEX IF NOT EXISTS idx_foods_date_marker ON foods(date, marker);

-- Daily snapshots
CREATE TABLE IF NOT EXISTS daily_snapshots (
    date DATE PRIMARY KEY,
    calories INTEGER NOT NULL,
    protein_g REAL NOT NULL,
    carbs_g REAL NOT NULL,
    fats_g REAL NOT NULL,
    sodium_mg INTEGER NOT NULL,
    snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Body measurements
CREATE TABLE IF NOT EXISTS body_measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    time TIME NOT NULL,
    weight_lbs REAL,
    waist_cm REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (weight_lbs IS NOT NULL OR waist_cm IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_body_date ON body_measurements(date);

-- Exercises
CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    exercise_type TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_exercises_date ON exercises(date);

-- Supplements (v2: dosage split into amount + unit)
CREATE TABLE IF NOT EXISTS supplements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    dosage_amount REAL NOT NULL,
    dosage_unit TEXT NOT NULL,
    purpose TEXT NOT NULL,
    time_of_day TEXT NOT NULL CHECK (time_of_day IN ('morning', 'midday', 'afternoon', 'evening', 'bedtime')),
    with_food BOOLEAN NOT NULL DEFAULT 0,
    notes TEXT,
    start_date DATE NOT NULL,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_supplements_dates ON supplements(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_supplements_time ON supplements(time_of_day);

-- Phases
CREATE TABLE IF NOT EXISTS phases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_recurring BOOLEAN NOT NULL DEFAULT 0,
    recurrence_interval_days INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_phases_dates ON phases(start_date, end_date);
"""


async def init_db(db_path: str | None = None):
    """Initialize the database with schema."""
    path = db_path or settings.health_tracker_database_path
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(path) as db:
        # Check if supplements table needs migration (v1 -> v2)
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='supplements'")
        table_exists = await cursor.fetchone()

        if table_exists:
            # Check if old schema (has 'dosage' column instead of 'dosage_amount')
            cursor = await db.execute("PRAGMA table_info(supplements)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]

            if 'dosage' in column_names and 'dosage_amount' not in column_names:
                # Migrate: drop old table and let new schema create it
                # Note: This loses data, but supplements feature is new
                await db.execute("DROP TABLE supplements")
                await db.commit()

        await db.executescript(SCHEMA)
        await db.commit()


@asynccontextmanager
async def get_db(db_path: str | None = None):
    """Get a database connection."""
    path = db_path or settings.health_tracker_database_path
    db = await aiosqlite.connect(path)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()
