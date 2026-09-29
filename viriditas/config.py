"""Load and validate the TOML configuration."""

from __future__ import annotations

import datetime as dt
import re
import tomllib
from dataclasses import dataclass, replace
from pathlib import Path

TZ_PATTERN = re.compile(r"^[+-]\d{4}$")

DEFAULT_CONFIG_NAME = "viriditas.toml"

# Lowest Unix timestamp we are willing to write. Timestamp 0 is avoided on
# purpose: some tools read it as "no date at all".
MIN_UNIX = 1

# Oldest reachable day. Git stores dates as Unix timestamps, so 1970-01-01 UTC
# is the floor; 1969-12-31 is only reachable through a negative UTC offset.
EARLIEST_START = dt.date(1969, 12, 31)

DEFAULT_MESSAGES = ["update", "tweak", "sync", "wip", "chore", "fix", "notes"]


class ConfigError(Exception):
    """Invalid configuration, with a message meant for the user."""


@dataclass(frozen=True)
class Config:
    """Every knob the tool exposes, already validated."""

    # [github]
    repo_name: str
    private: bool
    name: str
    email: str
    # [range]
    start: dt.date
    end: dt.date
    # [density]
    target_per_year: int
    min_per_day: int
    max_per_day: int
    weekend_factor: float
    seed: int
    timezone: str
    # [commit]
    messages: tuple[str, ...]
    activity_file: str
    add_readme: bool
    # [local]
    workdir: Path
    # where this came from
    source: Path

    @property
    def tz_offset_seconds(self) -> int:
        """'-0300' -> -10800."""
        sign = -1 if self.timezone[0] == "-" else 1
        hours = int(self.timezone[1:3])
        minutes = int(self.timezone[3:5])
        return sign * (hours * 3600 + minutes * 60)

    def with_identity(self, name: str, email: str) -> Config:
        return replace(self, name=name, email=email)


def _require(table: dict, section: str, key: str):
    if key not in table:
        raise ConfigError(f"missing required key [{section}].{key}")
    return table[key]


def _parse_date(value: str, field: str) -> dt.date:
    if value == "today":
        return dt.date.today()
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        raise ConfigError(
            f"[range].{field} = {value!r} is not a YYYY-MM-DD date (or 'today')"
        ) from None


def load(path: str | Path = DEFAULT_CONFIG_NAME) -> Config:
    """Read a config file and validate it."""
    path = Path(path)
    if not path.exists():
        raise ConfigError(
            f"config file not found: {path}\n"
            "Run `viriditas init` to create one from the template."
        )

    try:
        with path.open("rb") as handle:
            raw = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path} is not valid TOML: {exc}") from None

    github = raw.get("github", {})
    date_range = raw.get("range", {})
    density = raw.get("density", {})
    commit = raw.get("commit", {})
    local = raw.get("local", {})

    repo_name = str(_require(github, "github", "repo_name")).strip()
    if not repo_name or "/" in repo_name:
        raise ConfigError(
            "[github].repo_name must be a bare repository name, without the "
            "owner prefix and not empty"
        )

    messages = commit.get("messages", DEFAULT_MESSAGES)
    if not isinstance(messages, list) or not messages:
        raise ConfigError("[commit].messages must be a non-empty list of strings")

    config = Config(
        repo_name=repo_name,
        private=bool(github.get("private", True)),
        name=str(github.get("name", "auto")),
        email=str(github.get("email", "auto")),
        start=_parse_date(str(_require(date_range, "range", "start")), "start"),
        end=_parse_date(str(date_range.get("end", "today")), "end"),
        target_per_year=int(_require(density, "density", "target_per_year")),
        min_per_day=int(density.get("min_per_day", 1)),
        max_per_day=int(density.get("max_per_day", 14)),
        weekend_factor=float(density.get("weekend_factor", 1.0)),
        seed=int(density.get("seed", 42)),
        timezone=str(density.get("timezone", "+0000")),
        messages=tuple(str(item) for item in messages),
        activity_file=str(commit.get("file", "activity.log")),
        add_readme=bool(commit.get("add_readme", True)),
        workdir=Path(str(local.get("workdir", "./build/contribution-canvas"))),
        source=path.resolve(),
    )
    validate(config)
    return config


def validate(config: Config) -> None:
    """Reject configurations that cannot produce a valid repository."""
    if config.start < EARLIEST_START:
        raise ConfigError(
            f"[range].start = {config.start} is before {EARLIEST_START}. "
            "Git stores dates as Unix timestamps, so 1969-12-31 (with a "
            "negative UTC offset) is the oldest reachable day."
        )
    if config.end < config.start:
        raise ConfigError(
            f"[range].end ({config.end}) is before [range].start ({config.start})"
        )
    if config.end > dt.date.today():
        raise ConfigError(
            f"[range].end ({config.end}) is in the future; commits dated in the "
            "future are not counted on the contribution graph"
        )
    if config.min_per_day < 1:
        raise ConfigError("[density].min_per_day must be >= 1")
    if config.max_per_day < config.min_per_day:
        raise ConfigError("[density].max_per_day must be >= [density].min_per_day")
    if not 0 < config.weekend_factor <= 1:
        raise ConfigError("[density].weekend_factor must be within (0, 1]")
    if not TZ_PATTERN.match(config.timezone):
        raise ConfigError(
            f"[density].timezone = {config.timezone!r} must look like "
            "'+HHMM' or '-HHMM', for example '-0300'"
        )
    if config.start <= EARLIEST_START and config.tz_offset_seconds >= 0:
        raise ConfigError(
            "reaching 1969-12-31 requires a negative [density].timezone "
            "(for example '-0300'); with a non-negative offset that day would "
            "fall before the Unix epoch"
        )
    if "/" in config.activity_file or "\\" in config.activity_file:
        raise ConfigError("[commit].file must be a file name, not a path")

    # The yearly target has to be reachable between min and max per day.
    floor = 365 * config.min_per_day
    ceiling = 365 * config.max_per_day
    if config.target_per_year < floor:
        raise ConfigError(
            f"[density].target_per_year ({config.target_per_year}) is below the "
            f"forced minimum for a year (365 x min_per_day = {floor})"
        )
    if config.target_per_year > ceiling:
        raise ConfigError(
            f"[density].target_per_year ({config.target_per_year}) is above the "
            f"maximum for a year (365 x max_per_day = {ceiling})"
        )
