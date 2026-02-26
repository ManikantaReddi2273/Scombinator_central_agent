"""
Business date/time in app timezone (default Asia/Kolkata).
Use for CRM dates (LEADS, ACTIVITIES, TASKS). DB timestamps remain UTC.
Falls back to fixed UTC+5:30 (IST) when zoneinfo data is missing (e.g. Windows/minimal Docker).
"""
from datetime import datetime, date, timezone, timedelta, tzinfo

from config import settings

# IST = UTC+5:30 (no DST in India). Used when ZoneInfo("Asia/Kolkata") is not available.
_IST_FALLBACK = timezone(timedelta(hours=5, minutes=30))


def get_app_tz() -> tzinfo:
    """Return app timezone (e.g. Asia/Kolkata). Falls back to fixed UTC+5:30 if zoneinfo missing."""
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(settings.APP_TIMEZONE)
    except Exception:
        pass
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("Asia/Kolkata")
    except Exception:
        pass
    return _IST_FALLBACK


def now_ist() -> datetime:
    """Current datetime in app timezone (e.g. IST)."""
    return datetime.now(get_app_tz())


def today_ist() -> date:
    """Current date in app timezone (e.g. IST)."""
    return now_ist().date()


def today_ist_str(fmt: str = "%Y-%m-%d") -> str:
    """Current date in app timezone as string (YYYY-MM-DD)."""
    return today_ist().strftime(fmt)


def now_ist_str(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Current datetime in app timezone as string."""
    return now_ist().strftime(fmt)
