"""Render the schedule as a GitHub-style heatmap in the terminal."""

from __future__ import annotations

import datetime as dt
import sys

# Five intensity levels, empty to full. Some terminals (notably the Windows
# console under a legacy code page) cannot encode the block characters, so an
# ASCII set is kept as a fallback.
LEVELS_UNICODE = ["·", "░", "▒", "▓", "█"]
LEVELS_ASCII = [".", "-", "+", "*", "#"]

WEEKDAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
MONTH_INITIALS = "JFMAMJJASOND"

WEEKS = 53
LABEL_WIDTH = 5


def pick_levels(stream=None) -> list[str]:
    """Unicode blocks when the output stream can encode them, ASCII otherwise."""
    stream = stream or sys.stdout
    encoding = getattr(stream, "encoding", None) or "ascii"
    try:
        "".join(LEVELS_UNICODE).encode(encoding)
    except (UnicodeEncodeError, LookupError):
        return LEVELS_ASCII
    return LEVELS_UNICODE


def _level(count: int, ceiling: int) -> int:
    """0 for an empty day, 1..4 for increasing intensity."""
    if count <= 0:
        return 0
    if ceiling <= 1:
        return 4
    step = max(1, round(ceiling / 4))
    return min(4, max(1, -(-count // step)))


def _grid_start(year: int) -> dt.date:
    """The Sunday of the week containing January 1st (columns are weeks)."""
    jan1 = dt.date(year, 1, 1)
    # weekday(): 0=Monday .. 6=Sunday -> step back to the preceding Sunday
    return jan1 - dt.timedelta(days=(jan1.weekday() + 1) % 7)


def heatmap(
    schedule: dict[dt.date, int],
    year: int,
    ceiling: int,
    levels: list[str] | None = None,
) -> str:
    """7 rows (Sun..Sat) by 53 columns (weeks) for the requested year."""
    levels = levels or pick_levels()
    start = _grid_start(year)

    # Month initial on the column where that month starts.
    header = [" "] * WEEKS
    for week in range(WEEKS):
        for offset in range(7):
            day = start + dt.timedelta(days=week * 7 + offset)
            if day.year == year and day.day == 1:
                header[week] = MONTH_INITIALS[day.month - 1]
                break

    pad = " " * LABEL_WIDTH
    lines = [pad + "".join(header)]
    for row in range(7):
        cells = []
        for week in range(WEEKS):
            day = start + dt.timedelta(days=week * 7 + row)
            if day.year != year or day not in schedule:
                cells.append(" ")
            else:
                cells.append(levels[_level(schedule[day], ceiling)])
        lines.append(f"{WEEKDAY_LABELS[row]:<{LABEL_WIDTH}}" + "".join(cells))

    lines.append(pad + "less " + "".join(levels) + " more")
    return "\n".join(lines)
