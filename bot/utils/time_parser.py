import re
from datetime import timedelta
from typing import Optional

TIME_RE = re.compile(r"(\d+)\s*([s|m|h|d|w])", re.IGNORECASE)

UNIT_MAP = {
    "s": "seconds",
    "m": "minutes",
    "h": "hours",
    "d": "days",
    "w": "weeks",
}


def parse_time(time_str: str) -> Optional[timedelta]:
    """Parse a time string like '1h30m', '2d', '1w' into a timedelta object.
    
    Returns None if the string does not contain valid time format.
    """
    if not time_str:
        return None

    matches = TIME_RE.findall(time_str)
    if not matches:
        return None

    kwargs = {}
    for value_str, unit in matches:
        unit_key = UNIT_MAP[unit.lower()]
        val = int(value_str)
        kwargs[unit_key] = kwargs.get(unit_key, 0) + val

    if not kwargs:
        return None

    return timedelta(**kwargs)
