"""Tests for the distribution engine and the timestamp arithmetic.

Run with `python -m pytest`, or directly with `python tests/test_schedule.py`
(there is a tiny runner at the bottom for environments without pytest).
"""

from __future__ import annotations

import calendar
import datetime as dt
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from viriditas import generator, preview, schedule  # noqa: E402
from viriditas.config import Config, ConfigError, validate  # noqa: E402

TOLERANCE = 0.05
OFFSET = -10_800  # -0300


def make_config(**overrides) -> Config:
    base = dict(
        repo_name="test-canvas",
        private=True,
        name="Tester",
        email="tester@example.com",
        start=dt.date(1969, 12, 31),
        end=dt.date(2024, 12, 31),
        target_per_year=2000,
        min_per_day=1,
        max_per_day=14,
        weekend_factor=0.75,
        seed=42,
        timezone="-0300",
        messages=("update", "tweak"),
        activity_file="activity.log",
        add_readme=True,
        workdir=Path("./build/test-canvas"),
        source=Path("viriditas.toml"),
    )
    base.update(overrides)
    return Config(**base)


def full_years(config: Config) -> list[int]:
    return [
        year
        for year in range(config.start.year, config.end.year + 1)
        if dt.date(year, 1, 1) >= config.start
        and dt.date(year, 12, 31) <= config.end
    ]


# ------------------------------------------------------------ determinism


def test_same_seed_same_schedule():
    config = make_config()
    assert schedule.build(config) == schedule.build(config)


def test_different_seed_different_schedule():
    first = schedule.build(make_config(seed=42))
    second = schedule.build(make_config(seed=43))
    assert first != second
    assert first.keys() == second.keys()


def test_year_is_independent_of_range():
    """Shrinking the range must not reshuffle the years that stayed in it."""
    wide = schedule.build(make_config())
    narrow = schedule.build(
        make_config(start=dt.date(1990, 1, 1), end=dt.date(1995, 12, 31))
    )
    for day, count in narrow.items():
        assert wide[day] == count, day


# ------------------------------------------------------------ bounds


def test_per_day_limits_are_respected():
    config = make_config()
    counts = schedule.build(config).values()
    assert min(counts) >= config.min_per_day
    assert max(counts) <= config.max_per_day


def test_yearly_total_within_tolerance():
    config = make_config()
    totals = schedule.totals_by_year(schedule.build(config))
    for year in full_years(config):
        drift = abs(totals[year] - config.target_per_year) / config.target_per_year
        assert drift <= TOLERANCE, (year, totals[year])


def test_no_missing_day():
    config = make_config()
    plan = schedule.build(config)
    assert len(plan) == (config.end - config.start).days + 1
    day = config.start
    while day <= config.end:
        assert day in plan, day
        day += dt.timedelta(days=1)


def test_leap_year():
    config = make_config(start=dt.date(2000, 1, 1), end=dt.date(2000, 12, 31))
    plan = schedule.build(config)
    assert calendar.isleap(2000)
    assert len(plan) == 366
    assert dt.date(2000, 2, 29) in plan


def test_non_leap_year():
    config = make_config(start=dt.date(1999, 1, 1), end=dt.date(1999, 12, 31))
    plan = schedule.build(config)
    assert not calendar.isleap(1999)
    assert len(plan) == 365
    assert len([day for day in plan if day.month == 2]) == 28


def test_1969_has_only_december_31st():
    plan = schedule.build(make_config())
    assert [day for day in plan if day.year == 1969] == [dt.date(1969, 12, 31)]


def test_weekends_are_lighter_on_average():
    plan = schedule.build(make_config())
    weekend = [n for day, n in plan.items() if day.weekday() >= 5]
    weekday = [n for day, n in plan.items() if day.weekday() < 5]
    assert sum(weekend) / len(weekend) < sum(weekday) / len(weekday)


def test_partial_year_is_prorated():
    config = make_config(start=dt.date(2020, 1, 1), end=dt.date(2020, 6, 30))
    totals = schedule.totals_by_year(schedule.build(config))
    expected = config.target_per_year * 182 / 366
    assert abs(totals[2020] - expected) / expected <= TOLERANCE


def test_min_equals_max_is_flat():
    config = make_config(min_per_day=3, max_per_day=3, target_per_year=1095)
    assert set(schedule.build(config).values()) == {3}


# ------------------------------------------------------------ timestamps


def test_1969_window_starts_after_the_epoch():
    low, high = generator.day_window(dt.date(1969, 12, 31), OFFSET)
    assert low >= 1, "timestamp 0 is deliberately avoided"
    assert high == 10_799


def test_timestamps_always_land_on_the_right_day():
    rng = random.Random(7)
    for day in (
        dt.date(1969, 12, 31),
        dt.date(1970, 1, 1),
        dt.date(2000, 2, 29),
        dt.date(2024, 12, 31),
    ):
        for count in (1, 2, 14):
            stamps = generator.timestamps_for_day(day, count, OFFSET, rng)
            assert len(stamps) == count
            assert stamps == sorted(stamps)
            assert len(set(stamps)) == count
            for stamp in stamps:
                assert stamp > 0
                assert generator.unix_to_local_date(stamp, OFFSET) == day


def test_the_1969_trick():
    """Timestamp 3600 with offset -0300 is 1969-12-31 22:00 local."""
    assert generator.unix_to_local_string(3600, OFFSET) == "1969-12-31 22:00:00 -0300"


def test_raw_to_display():
    assert generator.raw_to_display("3600 -0300") == "1969-12-31 22:00:00 -0300"
    assert generator.raw_to_display("43200 +0000") == "1970-01-01 12:00:00 +0000"


def test_positive_offset_cannot_reach_1969():
    """A non-negative offset would place 1969-12-31 before the epoch."""
    config = make_config(timezone="+0000")
    try:
        validate(config)
    except ConfigError as exc:
        assert "negative" in str(exc)
    else:
        raise AssertionError("a positive offset with a 1969 start must be rejected")


def test_start_before_1969_is_rejected():
    config = make_config(start=dt.date(1969, 12, 30))
    try:
        validate(config)
    except ConfigError as exc:
        assert "1969-12-31" in str(exc)
    else:
        raise AssertionError("a start before 1969-12-31 must be rejected")


def test_unreachable_yearly_target_is_rejected():
    for bad in (make_config(target_per_year=100),
                make_config(target_per_year=999_999)):
        try:
            validate(bad)
        except ConfigError:
            pass
        else:
            raise AssertionError("an unreachable yearly target must be rejected")


# ------------------------------------------------------------ rendering


def test_heatmap_shape():
    config = make_config(start=dt.date(2024, 1, 1), end=dt.date(2024, 12, 31))
    plan = schedule.build(config)
    lines = preview.heatmap(
        plan, 2024, config.max_per_day, levels=preview.LEVELS_ASCII
    ).splitlines()
    # 1 month header + 7 weekday rows + 1 legend
    assert len(lines) == 9
    for row in lines[1:8]:
        assert len(row) == preview.LABEL_WIDTH + preview.WEEKS


def test_heatmap_falls_back_to_ascii():
    class Legacy:
        encoding = "cp1252"

    assert preview.pick_levels(Legacy()) == preview.LEVELS_ASCII


def test_plan_is_fast():
    config = make_config()
    started = time.perf_counter()
    schedule.build(config)
    assert time.perf_counter() - started < 3.0


if __name__ == "__main__":
    failures = 0
    for name, function in sorted(globals().items()):
        if not name.startswith("test_") or not callable(function):
            continue
        try:
            function()
            print(f"  pass  {name}")
        except AssertionError as exc:
            failures += 1
            print(f"  FAIL  {name}: {exc}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"  ERROR {name}: {type(exc).__name__}: {exc}")
    print(f"\n{failures} failure(s)")
    sys.exit(1 if failures else 0)
