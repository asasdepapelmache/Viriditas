"""Command line interface."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from . import __version__, generator, preview, publisher, schedule, undo
from .config import DEFAULT_CONFIG_NAME, ConfigError, load
from .generator import GenerateError
from .github import (
    ToolError,
    auth_status,
    gh_path,
    git_path,
    python_version,
)
from .publisher import PublishError
from .undo import UndoError

OK = "  ok  "
BAD = "  !!  "

TEMPLATE = '''# Viriditas configuration.
# Every value below is the default; delete what you do not want to change.

[github]
# The target repository. It MUST NOT EXIST YET, or must be empty: GitHub only
# indexes a full history on the first push to a fresh repository.
repo_name = "contribution-canvas"
private = true
# "auto" resolves from the authenticated account. The noreply address is always
# linked to the account, which is what makes commits count.
name = "auto"
email = "auto"

[range]
# 1969-12-31 is the oldest reachable day, and only with a negative timezone.
start = "1969-12-31"
end = "today"

[density]
target_per_year = 2000   # commits per full year, within 5%
min_per_day = 1          # every day gets at least this many
max_per_day = 14
weekend_factor = 0.75    # weekends slightly lighter
seed = 42                # same seed, same graph, forever
timezone = "-0300"       # offset written into every commit

[commit]
messages = ["update", "tweak", "sync", "wip", "chore", "fix", "notes"]
file = "activity.log"    # the single file every commit rewrites
add_readme = true        # explain the repository in its own README

[local]
workdir = "./build/contribution-canvas"
'''


def _force_utf8() -> None:
    """Terminals on a legacy code page cannot print the heatmap blocks."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def _confirm(question: str) -> bool:
    return input(f"{question} [y/N] ").strip().lower() in ("y", "yes")


def _resolved(config):
    """Config with name/email resolved, when either is still 'auto'."""
    if config.name == "auto" or config.email == "auto":
        identity = publisher.resolve_identity(config)
        return config.with_identity(identity["name"], identity["email"]), identity
    return config, publisher.resolve_identity(config)


# --------------------------------------------------------------- init


def cmd_init(args) -> int:
    path = Path(args.config)
    if path.exists() and not args.force:
        print(f"{path} already exists. Pass --force to overwrite it.")
        return 1
    path.write_text(TEMPLATE, encoding="utf-8")
    print(f"wrote {path}")
    print("\nEdit [github].repo_name, then run: viriditas check")
    return 0


# --------------------------------------------------------------- check


def cmd_check(args) -> int:
    print("Prerequisites:\n")
    problems: list[str] = []

    supported, version = python_version()
    print(f"{OK if supported else BAD}Python {version} (3.11+ required)")
    if not supported:
        problems.append("upgrade to Python 3.11 or newer")

    git_exe = git_path()
    print(f"{OK if git_exe else BAD}git: {git_exe or 'not found'}")
    if not git_exe:
        problems.append("install git")

    gh_exe = gh_path()
    print(f"{OK if gh_exe else BAD}gh:  {gh_exe or 'not found'}")
    if not gh_exe:
        problems.append("install the GitHub CLI: https://cli.github.com")

    authenticated = False
    if gh_exe:
        authenticated, detail = auth_status()
        print(f"{OK if authenticated else BAD}gh authentication")
        if authenticated:
            for line in detail.splitlines():
                if "Logged in" in line or "Token scopes" in line:
                    print(f"        {line.strip()}")
        else:
            problems.append("run: gh auth login")

    config = None
    try:
        config = load(args.config)
        print(f"{OK}config: {config.source}")
        visibility = "private" if config.private else "public"
        print(f"        repository: {config.repo_name} ({visibility})")
        print(f"        range: {config.start} to {config.end}  "
              f"offset {config.timezone}")
    except ConfigError as exc:
        print(f"{BAD}config: {exc}")
        problems.append("fix the configuration file")

    if config and authenticated:
        try:
            identity = publisher.resolve_identity(config)
            print(f"{OK}account: {identity['login']}")
            print(f"        commit author: {identity['name']} <{identity['email']}>")
        except ToolError as exc:
            print(f"{BAD}could not read the account: {exc}")
            problems.append("check your gh login")

    if problems:
        print("\nStill to do:")
        for item in problems:
            print(f"  - {item}")
        return 1

    print("\nAll good.")
    return 0


# --------------------------------------------------------------- plan


def _summary(config, plan) -> None:
    total = sum(plan.values())
    print(f"Range:    {config.start} to {config.end}  (offset {config.timezone})")
    print(f"Days:     {len(plan):,}")
    print(f"Commits:  {total:,}")
    print(f"Per day:  min {min(plan.values())} / max {max(plan.values())}  "
          f"(configured {config.min_per_day}..{config.max_per_day})")
    estimate = total / generator.ESTIMATED_COMMITS_PER_SECOND
    print(f"Estimated generate time: ~{estimate:.0f}s")
    print(f"Target per full year: {config.target_per_year:,} (within 5%)")

    totals = schedule.totals_by_year(plan)
    print("\nPer year:")
    years = sorted(totals)
    for row in range(0, len(years), 6):
        cells = [f"{year}: {totals[year]:>5,}" for year in years[row:row + 6]]
        print("  " + "   ".join(cells))


def cmd_plan(args) -> int:
    config = load(args.config)
    plan = schedule.build(config)

    if args.json:
        print(json.dumps(
            {
                "range": {"start": str(config.start), "end": str(config.end)},
                "total": sum(plan.values()),
                "days": len(plan),
                "per_year": schedule.totals_by_year(plan),
                "per_day": {str(k): v for k, v in sorted(plan.items())},
            },
            indent=2,
        ))
        return 0

    _summary(config, plan)

    year = args.year or config.end.year
    if year not in {day.year for day in plan}:
        print(f"\n{year} is outside the configured range; nothing to draw.")
        return 0
    print(f"\nHeatmap for {year}:\n")
    print(preview.heatmap(plan, year, config.max_per_day))
    return 0


# --------------------------------------------------------------- generate


def cmd_generate(args) -> int:
    config, _ = _resolved(load(args.config))
    print(f"Commit author: {config.name} <{config.email}>")

    plan = schedule.build(config)
    total = sum(plan.values())
    print(f"Generating {total:,} commits in {config.workdir} ...")

    result = generator.generate(config, plan, force=args.force)

    print(f"\nDone in {result['elapsed']:.1f}s")
    print(f"  commits written:  {result['commits_written']:,}")
    print(f"  commits on main:  {result['commits_in_repo']:,}")
    if result["commits_in_repo"] != total:
        print(f"{BAD}count does not match the plan ({total:,}).")
        return 1
    print(f"  first: {result['first']}")
    print(f"  last:  {result['last']}")
    print("\nNext: viriditas push")
    return 0


# --------------------------------------------------------------- push


def cmd_push(args) -> int:
    config = load(args.config)
    if not config.workdir.exists():
        raise PublishError(
            f"{config.workdir} does not exist. Run `viriditas generate` first."
        )

    local_count = generator.commit_count(config.workdir)
    if not local_count:
        raise PublishError(f"{config.workdir} has no commits on main.")

    identity = publisher.resolve_identity(config)
    owner = identity["login"]

    info = publisher.ensure_repo(config, owner)
    if info.get("created_now"):
        visibility = "private" if config.private else "public"
        print(f"  created {owner}/{config.repo_name} ({visibility})")
    publisher.ensure_private(config, owner, info)

    url = publisher.set_remote(config, owner, config.workdir)
    print(f"  remote: {url}")

    remote_count = publisher.remote_commit_count(config.workdir)
    if remote_count not in (None, 0):
        warning = publisher.describe_dirty_target(
            owner, config.repo_name, remote_count
        )
        if not args.force:
            raise PublishError(warning)
        print(f"\nWARNING: {warning}\n")
        print("  --force was given, so this will proceed, but the graph will "
              "most likely stay incomplete.")
        if not args.yes and not _confirm("Continue anyway?"):
            print("Cancelled.")
            return 1

    print(f"  pushing {local_count:,} commits...")
    publisher.push(config.workdir, force=args.force)
    publisher.ensure_default_branch(config, owner, info)

    print(f"\nPushed {local_count:,} commits to {url}")
    print(publisher.REMINDER)
    return 0


# --------------------------------------------------------------- run


def cmd_run(args) -> int:
    if cmd_check(args) != 0:
        print("\nFix the prerequisites before running.")
        return 1

    config = load(args.config)
    plan = schedule.build(config)
    print("\n" + "-" * 62)
    _summary(config, plan)
    print("-" * 62)
    print(f"\nThis will build {config.workdir} and push to {config.repo_name}.")

    if not args.yes and not _confirm("Generate and push?"):
        print("Cancelled.")
        return 1

    if cmd_generate(args) != 0:
        return 1
    return cmd_push(args)


# --------------------------------------------------------------- status


def cmd_status(args) -> int:
    config = load(args.config)
    print(f"Configured repository: {config.repo_name}")

    print("\nLocal:")
    if not config.workdir.exists():
        print(f"  {config.workdir} does not exist (nothing generated yet).")
    else:
        count = generator.commit_count(config.workdir)
        print(f"  {config.workdir}")
        print(f"  commits: {count:,}" if count else "  commits: ?")
        bounds = generator.raw_bounds(config.workdir)
        if bounds:
            print(f"  first: {generator.raw_to_display(bounds[0])}")
            print(f"  last:  {generator.raw_to_display(bounds[1])}")

    print("\nGitHub:")
    try:
        identity = publisher.resolve_identity(config)
    except ToolError as exc:
        print(f"  could not reach gh: {exc}")
        return 1

    owner = identity["login"]
    from .github import repo_info

    info = repo_info(owner, config.repo_name)
    if info is None:
        print(f"  {owner}/{config.repo_name} does not exist yet.")
        print("  (good: an empty target is exactly what a first push needs)")
        return 0

    print(f"  {info.get('url')}")
    print(f"  visibility: {info.get('visibility')}  |  fork: {info.get('isFork')}"
          f"  |  default branch: "
          f"{(info.get('defaultBranchRef') or {}).get('name')}")
    if config.workdir.exists():
        remote_count = publisher.remote_commit_count(config.workdir)
        if remote_count is not None:
            shown = remote_count if remote_count >= 0 else "?"
            print(f"  commits on remote main: {shown}")
    print(f"\n  commit author: {identity['name']} <{identity['email']}>")
    if info.get("visibility", "").upper() == "PRIVATE":
        print("  reminder: private contributions must be enabled at")
        print("  https://github.com/settings/profile")
    return 0


# --------------------------------------------------------------- topup


def cmd_topup(args) -> int:
    config, _ = _resolved(load(args.config))
    if not config.workdir.exists():
        raise GenerateError(
            f"{config.workdir} does not exist; nothing to top up. "
            "Run `viriditas run` first."
        )

    bounds = generator.raw_bounds(config.workdir)
    if bounds is None:
        raise GenerateError("the local repository has no commits.")

    stamp_text, tz_text = bounds[1].split()
    sign = -1 if tz_text[0] == "-" else 1
    offset = sign * (int(tz_text[1:3]) * 3600 + int(tz_text[3:5]) * 60)
    last_day = generator.unix_to_local_date(int(stamp_text), offset)

    today = dt.date.today()
    if last_day >= today:
        print(f"Last commit is dated {last_day}; nothing to top up.")
        return 0

    full = schedule.build(config)
    missing = {day: n for day, n in full.items() if last_day < day <= today}
    if not missing:
        print("Nothing to top up inside the configured range.")
        return 0

    print(f"Last commit: {last_day}. Filling up to {today}.")
    print(f"  {len(missing)} day(s), {sum(missing.values()):,} commits")
    if not args.yes and not _confirm("Generate and push?"):
        print("Cancelled.")
        return 1

    generator.append(config, missing)
    return cmd_push(args)


# --------------------------------------------------------------- clean


def cmd_clean(args) -> int:
    config = load(args.config)
    if not config.workdir.exists():
        print(f"{config.workdir} does not exist; nothing to clean.")
        return 0
    count = generator.commit_count(config.workdir)
    print(f"About to delete the local folder {config.workdir}"
          f"{f' ({count:,} commits)' if count else ''}.")
    print("The remote repository is not touched.")
    if not args.yes and not _confirm("Delete it?"):
        print("Cancelled.")
        return 1
    undo.clean(config)
    return 0


# --------------------------------------------------------------- undo


def cmd_undo(args) -> int:
    config = load(args.config)
    if args.hide:
        undo.hide()
        return 0
    identity = publisher.resolve_identity(config)
    undo.delete(config, identity["login"], confirm=_ask_name)
    return 0


def _ask_name(expected: str) -> str:
    return input(f"  type `{expected}` to confirm: ")


# --------------------------------------------------------------- parser


COMMANDS = {
    "init": cmd_init,
    "check": cmd_check,
    "plan": cmd_plan,
    "generate": cmd_generate,
    "push": cmd_push,
    "run": cmd_run,
    "status": cmd_status,
    "topup": cmd_topup,
    "clean": cmd_clean,
    "undo": cmd_undo,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="viriditas",
        description="Fill a GitHub contribution graph with backdated commits.",
    )
    parser.add_argument("--version", action="version", version=f"viriditas {__version__}")
    parser.add_argument(
        "--config", default=DEFAULT_CONFIG_NAME,
        help=f"path to the configuration file (default: {DEFAULT_CONFIG_NAME})",
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>")

    init = sub.add_parser("init", help="write a starter configuration file")
    init.add_argument("--force", action="store_true", help="overwrite an existing file")

    sub.add_parser("check", help="verify git, gh, authentication and the config")

    plan = sub.add_parser("plan", help="dry run: totals, estimate and heatmap")
    plan.add_argument("--year", type=int, help="year to draw (default: the last one)")
    plan.add_argument("--json", action="store_true", help="machine readable output")

    gen = sub.add_parser("generate", help="build the local repository")
    gen.add_argument("--force", action="store_true", help="rebuild an existing workdir")

    push = sub.add_parser("push", help="create the repository and push")
    push.add_argument("--force", action="store_true",
                      help="push onto a non-empty target (not recommended)")
    push.add_argument("-y", "--yes", action="store_true", help="skip confirmation")

    run = sub.add_parser("run", help="check, generate and push in one go")
    run.add_argument("--force", action="store_true")
    run.add_argument("-y", "--yes", action="store_true", help="skip confirmation")

    sub.add_parser("status", help="show the local and remote state")

    topup = sub.add_parser("topup", help="fill the days missing since the last commit")
    topup.add_argument("-y", "--yes", action="store_true", help="skip confirmation")
    topup.add_argument("--force", action="store_true")

    clean = sub.add_parser("clean", help="delete the local workdir, keep the remote")
    clean.add_argument("-y", "--yes", action="store_true", help="skip confirmation")

    undo_parser = sub.add_parser("undo", help="hide from the graph, or delete for good")
    mode = undo_parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--hide", action="store_true",
                      help="print how to hide the graph without deleting anything")
    mode.add_argument("--delete", action="store_true",
                      help="delete the remote repository and the local folder")

    return parser


def main(argv: list[str] | None = None) -> int:
    _force_utf8()
    args = build_parser().parse_args(argv)
    for flag in ("force", "yes", "json", "year"):
        if not hasattr(args, flag):
            setattr(args, flag, False if flag != "year" else None)
    try:
        return COMMANDS[args.command](args)
    except (ConfigError, ToolError, GenerateError, PublishError, UndoError) as exc:
        print(f"\nerror: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\ninterrupted.", file=sys.stderr)
        return 130
