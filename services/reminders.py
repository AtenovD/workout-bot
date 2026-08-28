"""
Reminder scheduling service.
"""
from datetime import datetime, time
import pytz
from dataclasses import dataclass
from typing import Optional


@dataclass
class ReminderConfig:
    user_id: int
    days_of_week: list[int]  # 1=Mon, 7=Sun
    reminder_time: time
    timezone: str
    enabled: bool = True


def get_next_reminder_dt(config: ReminderConfig) -> Optional[datetime]:
    """Calculate next reminder datetime in UTC."""
    if not config.enabled or not config.days_of_week:
        return None

    tz = pytz.timezone(config.timezone)
    now = datetime.now(tz)

    for days_ahead in range(8):
        candidate = now.replace(
            hour=config.reminder_time.hour,
            minute=config.reminder_time.minute,
            second=0,
            microsecond=0,
        )
        from datetime import timedelta
        candidate += timedelta(days=days_ahead)
        weekday = candidate.isoweekday()  # 1=Mon, 7=Sun
        if weekday in config.days_of_week and candidate > now:
            return candidate.astimezone(pytz.utc)

    return None
