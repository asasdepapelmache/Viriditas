"""Decide how many commits land on each day of the range.

Pure and deterministic: the same configuration and seed always produce the same
schedule. Each year draws from its own generator, seeded with `seed:year`, so
changing the range does not reshuffle the years that stayed inside it.
"""

from __future__ import annotations

import calendar
import datetime as dt
import random

from .config import Config

# Spread applied to each day's weight before it is normalised to the yearly
# target. Without it, every week would look identical.
JITTER_LOW = 0.55
JITTER_HIGH = 1.45


def days_in_year(year: int) -> int:
    return 366 if calendar.isleap(year) else 365


def iter_days(start: dt.date, end: dt.date):
    """Every day from start to end, inclusive."""
    day = start
    step = dt.timedelta(days=1)
    while day <= end:
        yield day
        day += step


def year_target(config: Config, year: int, day_count: int) -> int:
    """The yearly target, prorated when the range covers only part of a year."""
    total = days_in_year(year)
    if day_count >= total:
        return config.target_per_year
    return max(
        day_count * config.min_per_day,
        round(config.target_per_year * day_count / total),
    )


def _distribute(config: Config, year: int, days: list[dt.date]) -> dict[dt.date, int]:
    rng = random.Random(f"{config.seed}:{year}")
    counts = {day: config.min_per_day for day in days}

    target = year_target(config, year, len(days))
    headroom = config.max_per_day - config.min_per_day
    remaining = target - config.min_per_day * len(days)
    if remaining <= 0 or headroom == 0:
        return counts

    remaining = min(remaining, headroom * len(days))

    weights = {
        day: (config.weekend_factor if day.weekday() >= 5 else 1.0)
        * rng.uniform(JITTER_LOW, JITTER_HIGH)
        for day in days
    }
    total_weight = sum(weights.values())

    for day in days:
        extra = int(remaining * weights[day] / total_weight)
        counts[day] += min(extra, headroom)

    # Integer division and the clamp above leave a remainder. Hand it out one
    # commit at a time, weighted, so the yearly total lands exactly on target.
    leftover = target - sum(counts.values())
    while leftover > 0:
        open_days = [day for day in days if counts[day] < config.max_per_day]
        if not open_days:
            break
        pick = rng.choices(open_days, weights=[weights[d] for d in open_days])[0]
        counts[pick] += 1
        leftover -= 1
    while leftover < 0:
        open_days = [day for day in days if counts[day] > config.min_per_day]
        if not open_days:
            break
        pick = rng.choices(open_days, weights=[weights[d] for d in open_days])[0]
        counts[pick] -= 1
        leftover += 1

    return counts


def build(config: Config) -> dict[dt.date, int]:
    """{day: commit count} for every day in the configured range."""
    by_year: dict[int, list[dt.date]] = {}
    for day in iter_days(config.start, config.end):
        by_year.setdefault(day.year, []).append(day)

    schedule: dict[dt.date, int] = {}
    for year in sorted(by_year):
        schedule.update(_distribute(config, year, by_year[year]))
    return schedule


def totals_by_year(schedule: dict[dt.date, int]) -> dict[int, int]:
    totals: dict[int, int] = {}
    for day, count in schedule.items():
        totals[day.year] = totals.get(day.year, 0) + count
    return dict(sorted(totals.items()))
