"""
Withings data synchronization service.

Handles fetching data from Withings API and storing it in local database.
"""
from datetime import datetime, date, time
from typing import Any
import httpx
import logging

from app.database import get_db
from app.services import withings_service

logger = logging.getLogger(__name__)

WITHINGS_MEASURE_URL = "https://wbsapi.withings.net/measure"
WITHINGS_ACTIVITY_URL = "https://wbsapi.withings.net/v2/measure"
WITHINGS_SLEEP_URL = "https://wbsapi.withings.net/v2/sleep"

# Withings measurement type codes
MEAS_TYPE_WEIGHT = 1
MEAS_TYPE_FAT_MASS = 8
MEAS_TYPE_MUSCLE_MASS = 76
MEAS_TYPE_BONE_MASS = 88
MEAS_TYPE_BODY_WATER = 77
MEAS_TYPE_SYSTOLIC = 10
MEAS_TYPE_DIASTOLIC = 9
MEAS_TYPE_HEART_RATE = 11


def kg_to_lbs(kg: float) -> float:
    """Convert kilograms to pounds."""
    return kg * 2.20462


def meters_to_miles(m: float) -> float:
    """Convert meters to miles."""
    return m / 1609.344


def meters_to_feet(m: float) -> float:
    """Convert meters to feet."""
    return m * 3.28084


def parse_withings_value(value: int, unit: int) -> float:
    """Parse Withings measurement value with unit exponent."""
    return value * (10 ** unit)


async def fetch_measurements(start_date: date, end_date: date, meas_type: int | None = None) -> list[dict]:
    """Fetch measurements from Withings Measure API."""
    token = await withings_service.get_valid_token()
    if not token:
        logger.error("No valid token for fetching measurements")
        return []

    params = {
        "action": "getmeas",
        "startdate": int(datetime.combine(start_date, time.min).timestamp()),
        "enddate": int(datetime.combine(end_date, time.max).timestamp()),
    }
    if meas_type:
        params["meastype"] = meas_type

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                WITHINGS_MEASURE_URL,
                data=params,
                headers={"Authorization": f"Bearer {token}"},
            )
        data = response.json()
    except httpx.TimeoutException:
        logger.error("Timeout fetching measurements from Withings")
        return []
    except httpx.RequestError as e:
        logger.error(f"Network error fetching measurements: {e}")
        return []
    except ValueError as e:
        logger.error(f"Invalid JSON response from Withings: {e}")
        return []

    if data.get("status") != 0:
        logger.error(f"Withings API error: {data}")
        return []

    return data.get("body", {}).get("measuregrps", [])


async def sync_body_measurements(measure_groups: list[dict]) -> int:
    """Sync body measurements from Withings data. Returns count of new records."""
    count = 0

    for grp in measure_groups:
        grp_id = str(grp.get("grpid"))
        timestamp = grp.get("date")
        measures = grp.get("measures", [])

        # Check for duplicate
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id FROM body_measurements WHERE withings_id = ?",
                (grp_id,),
            )
            if await cursor.fetchone():
                continue  # Skip duplicate

        # Parse measurements
        weight_kg = None
        fat_mass_kg = None
        muscle_mass_kg = None
        bone_mass_kg = None
        body_water_pct = None

        for m in measures:
            value = parse_withings_value(m["value"], m["unit"])
            mtype = m["type"]

            if mtype == MEAS_TYPE_WEIGHT:
                weight_kg = value
            elif mtype == MEAS_TYPE_FAT_MASS:
                fat_mass_kg = value
            elif mtype == MEAS_TYPE_MUSCLE_MASS:
                muscle_mass_kg = value
            elif mtype == MEAS_TYPE_BONE_MASS:
                bone_mass_kg = value
            elif mtype == MEAS_TYPE_BODY_WATER:
                body_water_pct = value

        # Skip if no weight (we require weight for body measurements)
        if weight_kg is None:
            continue

        # Convert to US units
        weight_lbs = kg_to_lbs(weight_kg)
        fat_mass_lbs = kg_to_lbs(fat_mass_kg) if fat_mass_kg else None
        muscle_mass_lbs = kg_to_lbs(muscle_mass_kg) if muscle_mass_kg else None
        bone_mass_lbs = kg_to_lbs(bone_mass_kg) if bone_mass_kg else None

        # Parse timestamp
        dt = datetime.fromtimestamp(timestamp)
        meas_date = dt.date().isoformat()
        meas_time = dt.time().isoformat()

        # Insert into database
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO body_measurements
                (date, time, weight_lbs, waist_cm, fat_mass_lbs, muscle_mass_lbs, bone_mass_lbs, body_water_pct, source, withings_id)
                VALUES (?, ?, ?, NULL, ?, ?, ?, ?, 'withings', ?)
                """,
                (meas_date, meas_time, weight_lbs, fat_mass_lbs, muscle_mass_lbs, bone_mass_lbs, body_water_pct, grp_id),
            )
            await db.commit()
            count += 1

    return count


async def sync_blood_pressure(measure_groups: list[dict]) -> int:
    """Sync blood pressure from Withings data. Returns count of new records."""
    count = 0

    for grp in measure_groups:
        grp_id = str(grp.get("grpid"))
        timestamp = grp.get("date")
        measures = grp.get("measures", [])

        # Check for duplicate
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id FROM blood_pressure WHERE withings_id = ?",
                (grp_id,),
            )
            if await cursor.fetchone():
                continue

        # Parse measurements
        systolic = None
        diastolic = None
        heart_rate = None

        for m in measures:
            value = parse_withings_value(m["value"], m["unit"])
            mtype = m["type"]

            if mtype == MEAS_TYPE_SYSTOLIC:
                systolic = int(value)
            elif mtype == MEAS_TYPE_DIASTOLIC:
                diastolic = int(value)
            elif mtype == MEAS_TYPE_HEART_RATE:
                heart_rate = int(value)

        # Skip if no BP data
        if systolic is None or diastolic is None:
            continue

        # Parse timestamp
        dt = datetime.fromtimestamp(timestamp)
        meas_date = dt.date().isoformat()
        meas_time = dt.time().isoformat()

        # Insert into database
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO blood_pressure
                (date, time, systolic, diastolic, heart_rate, source, withings_id)
                VALUES (?, ?, ?, ?, ?, 'withings', ?)
                """,
                (meas_date, meas_time, systolic, diastolic, heart_rate, grp_id),
            )
            await db.commit()
            count += 1

    return count


async def fetch_activity(start_date: date, end_date: date) -> list[dict]:
    """Fetch activity data from Withings Activity API."""
    token = await withings_service.get_valid_token()
    if not token:
        logger.error("No valid token for fetching activity")
        return []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                WITHINGS_ACTIVITY_URL,
                data={
                    "action": "getactivity",
                    "startdateymd": start_date.isoformat(),
                    "enddateymd": end_date.isoformat(),
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        data = response.json()
    except httpx.TimeoutException:
        logger.error("Timeout fetching activity from Withings")
        return []
    except httpx.RequestError as e:
        logger.error(f"Network error fetching activity: {e}")
        return []
    except ValueError as e:
        logger.error(f"Invalid JSON response from Withings activity API: {e}")
        return []

    if data.get("status") != 0:
        logger.error(f"Withings Activity API error: {data}")
        return []

    return data.get("body", {}).get("activities", [])


async def sync_activity(activities: list[dict]) -> int:
    """Sync activity data from Withings. Returns count of upserted records."""
    count = 0

    for act in activities:
        act_date = act.get("date")
        if not act_date:
            continue

        steps = act.get("steps")
        distance_m = act.get("distance")
        active_calories = act.get("calories")
        elevation_m = act.get("elevation")

        # Convert units
        distance_miles = meters_to_miles(distance_m) if distance_m else None
        elevation_ft = meters_to_feet(elevation_m) if elevation_m else None

        # Upsert into database (one row per day)
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id FROM daily_activity WHERE date = ?",
                (act_date,),
            )
            existing = await cursor.fetchone()

            if existing:
                await db.execute(
                    """
                    UPDATE daily_activity
                    SET steps = ?, distance_miles = ?, active_calories = ?, elevation_ft = ?,
                        source = 'withings', updated_at = CURRENT_TIMESTAMP
                    WHERE date = ?
                    """,
                    (steps, distance_miles, active_calories, elevation_ft, act_date),
                )
            else:
                await db.execute(
                    """
                    INSERT INTO daily_activity
                    (date, steps, distance_miles, active_calories, elevation_ft, source)
                    VALUES (?, ?, ?, ?, ?, 'withings')
                    """,
                    (act_date, steps, distance_miles, active_calories, elevation_ft),
                )
            await db.commit()
            count += 1

    return count


async def fetch_sleep(start_date: date, end_date: date) -> list[dict]:
    """Fetch sleep data from Withings Sleep API."""
    token = await withings_service.get_valid_token()
    if not token:
        logger.error("No valid token for fetching sleep")
        return []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                WITHINGS_SLEEP_URL,
                data={
                    "action": "getsummary",
                    "startdateymd": start_date.isoformat(),
                    "enddateymd": end_date.isoformat(),
                },
                headers={"Authorization": f"Bearer {token}"},
            )
        data = response.json()
    except httpx.TimeoutException:
        logger.error("Timeout fetching sleep from Withings")
        return []
    except httpx.RequestError as e:
        logger.error(f"Network error fetching sleep: {e}")
        return []
    except ValueError as e:
        logger.error(f"Invalid JSON response from Withings sleep API: {e}")
        return []

    if data.get("status") != 0:
        logger.error(f"Withings Sleep API error: {data}")
        return []

    return data.get("body", {}).get("series", [])


async def sync_sleep(sleep_data: list[dict]) -> int:
    """Sync sleep data from Withings. Returns count of new records."""
    count = 0

    for sleep in sleep_data:
        sleep_id = str(sleep.get("id", sleep.get("date", "")))
        sleep_date = sleep.get("date")

        if not sleep_date:
            continue

        # Check for duplicate
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id FROM sleep WHERE withings_id = ?",
                (sleep_id,),
            )
            if await cursor.fetchone():
                continue

        # Parse sleep data
        startdate = sleep.get("startdate")
        enddate = sleep.get("enddate")
        data = sleep.get("data", {})

        sleep_start = datetime.fromtimestamp(startdate).isoformat() if startdate else None
        sleep_end = datetime.fromtimestamp(enddate).isoformat() if enddate else None

        # Duration in seconds, convert to minutes
        duration_seconds = data.get("durationtosleep", 0) + data.get("durationtowakeup", 0)
        total_sleep_seconds = data.get("deepsleepduration", 0) + data.get("lightsleepduration", 0) + data.get("remsleepduration", 0)

        duration_minutes = total_sleep_seconds // 60 if total_sleep_seconds else None
        deep_minutes = data.get("deepsleepduration", 0) // 60 if data.get("deepsleepduration") else None
        light_minutes = data.get("lightsleepduration", 0) // 60 if data.get("lightsleepduration") else None
        rem_minutes = data.get("remsleepduration", 0) // 60 if data.get("remsleepduration") else None
        awake_minutes = data.get("wakeupduration", 0) // 60 if data.get("wakeupduration") else None

        # Insert into database
        async with get_db() as db:
            await db.execute(
                """
                INSERT INTO sleep
                (date, sleep_start, sleep_end, duration_minutes, deep_minutes, light_minutes, rem_minutes, awake_minutes, source, withings_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'withings', ?)
                """,
                (sleep_date, sleep_start, sleep_end, duration_minutes, deep_minutes, light_minutes, rem_minutes, awake_minutes, sleep_id),
            )
            await db.commit()
            count += 1

    return count


async def sync_by_appli(appli: int, startdate: int | None = None, enddate: int | None = None) -> int:
    """Sync data for a specific Withings appli code. Returns count of synced records."""
    # Default to last 7 days if no dates provided
    if startdate and enddate:
        start = date.fromtimestamp(startdate)
        end = date.fromtimestamp(enddate)
    else:
        end = date.today()
        start = date.fromordinal(end.toordinal() - 7)

    if appli == 1:  # Weight/Body composition
        groups = await fetch_measurements(start, end)
        return await sync_body_measurements(groups)
    elif appli == 4:  # Blood pressure
        groups = await fetch_measurements(start, end)
        return await sync_blood_pressure(groups)
    elif appli == 16:  # Activity
        activities = await fetch_activity(start, end)
        return await sync_activity(activities)
    elif appli == 44:  # Sleep
        sleep_data = await fetch_sleep(start, end)
        return await sync_sleep(sleep_data)
    else:
        logger.warning(f"Unknown appli code: {appli}")
        return 0


async def backfill_all(start_date: date, end_date: date) -> dict[str, int]:
    """Backfill all data types for a date range. Returns counts by type."""
    counts = {
        "body_measurements": 0,
        "blood_pressure": 0,
        "daily_activity": 0,
        "sleep": 0,
    }

    # Fetch and sync body measurements (includes weight + body comp)
    groups = await fetch_measurements(start_date, end_date)
    counts["body_measurements"] = await sync_body_measurements(groups)
    counts["blood_pressure"] = await sync_blood_pressure(groups)

    # Fetch and sync activity
    activities = await fetch_activity(start_date, end_date)
    counts["daily_activity"] = await sync_activity(activities)

    # Fetch and sync sleep
    sleep_data = await fetch_sleep(start_date, end_date)
    counts["sleep"] = await sync_sleep(sleep_data)

    return counts


async def backfill_full_history() -> dict[str, int]:
    """Backfill all available historical data."""
    # Withings typically allows 2 years of history
    end = date.today()
    start = date.fromordinal(end.toordinal() - 730)  # ~2 years
    return await backfill_all(start, end)
