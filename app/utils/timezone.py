"""Timezone utilities for converting UTC to user timezone."""
from datetime import datetime, date, time
from zoneinfo import ZoneInfo


def convert_datetime_to_tz(dt: datetime, timezone: str | None) -> datetime:
    """Convert a naive UTC datetime to the specified timezone."""
    if timezone is None:
        return dt
    try:
        utc_dt = dt.replace(tzinfo=ZoneInfo("UTC"))
        return utc_dt.astimezone(ZoneInfo(timezone)).replace(tzinfo=None)
    except Exception:
        return dt


def convert_date_time_to_tz(d: date, t: time, timezone: str | None) -> tuple[date, time]:
    """Convert a date and time (assumed UTC) to the specified timezone."""
    if timezone is None:
        return d, t
    try:
        dt = datetime.combine(d, t)
        converted = convert_datetime_to_tz(dt, timezone)
        return converted.date(), converted.time()
    except Exception:
        return d, t


def current_date_in_timezone(timezone: str | None) -> date:
    """Return today's date in the given timezone (falls back to server date on errors)."""
    if timezone:
        try:
            return datetime.now(ZoneInfo(timezone)).date()
        except Exception:
            pass
    return date.today()
