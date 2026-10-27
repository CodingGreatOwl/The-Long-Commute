from __future__ import annotations

import re

_TIME_RE = re.compile(r"^(\d{1,2}):(\d{2}):(\d{2})$")


def hhmmss_to_secs(value: str) -> int:
    match = _TIME_RE.match(value.strip())
    if not match:
        raise ValueError(f"Invalid GTFS time: {value!r}")
    hours, minutes, seconds = (int(part) for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def secs_to_hhmmss(total_seconds: int) -> str:
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
