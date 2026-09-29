"""Create the remote repository and push the generated history."""

from __future__ import annotations

from pathlib import Path

from .config import Config
from .github import ToolError, current_user, gh, git, repo_info

REMOTE = "origin"


class PublishError(Exception):
    """Publishing failed, with a message meant for the user."""


# Pushing onto a repository that already has commits is the one mistake that
# silently produces a half-empty graph. See the README for the measurements.
DIRTY_TARGET = """{owner}/{repo} already has {count} commit(s) on main.

GitHub only indexes a full history on the FIRST push to a freshly created
repository. Pushing on top of an existing history indexes only part of the
commits -- even with --force, and even though the push itself succeeds.

To get the whole graph, the target has to be empty:
  - point [github].repo_name at a repository that does not exist yet, or
  - delete and recreate {repo}, then push again."""


def resolve_identity(config: Config) -> dict:
    """Turn 'auto' name/email into the authenticated account's values."""
    user = current_user()
    return {
        "login": user["login"],
        "name": user["name"] if config.name == "auto" else config.name,
        "email": user["noreply_email"] if config.email == "auto" else config.email,
    }


def ensure_repo(config: Config, owner: str) -> dict:
    """Create the repository when missing; return its metadata either way."""
    info = repo_info(owner, config.repo_name)
    if info is None:
        gh(
            "repo", "create", config.repo_name,
            "--private" if config.private else "--public",
            "--description", "contribution graph, generated with Viriditas",
        )
        info = repo_info(owner, config.repo_name)
        if info is None:
            raise PublishError(
                f"created {owner}/{config.repo_name} but could not read it back."
            )
        info["created_now"] = True
        return info

    info["created_now"] = False
    if info.get("isFork"):
        raise PublishError(
            f"{owner}/{config.repo_name} is a fork. GitHub does not count "
            "contributions made in forks. Use a repository that is not a fork."
        )
    return info


def remote_commit_count(workdir: Path) -> int | None:
    """Commits on the remote main branch. None when there is no main branch."""
    listing = git("ls-remote", REMOTE, "refs/heads/main", cwd=workdir, check=False)
    if not listing.strip():
        return None
    try:
        git("fetch", "--quiet", REMOTE, "main", cwd=workdir)
        return int(git("rev-list", "--count", "FETCH_HEAD", cwd=workdir).strip())
    except (ToolError, ValueError):
        return -1  # the branch exists but could not be counted


def set_remote(config: Config, owner: str, workdir: Path) -> str:
    url = f"https://github.com/{owner}/{config.repo_name}.git"
    if REMOTE in git("remote", cwd=workdir).split():
        git("remote", "set-url", REMOTE, url, cwd=workdir)
    else:
        git("remote", "add", REMOTE, url, cwd=workdir)
    return url


def describe_dirty_target(owner: str, repo: str, count: int | None) -> str:
    return DIRTY_TARGET.format(
        owner=owner, repo=repo, count=count if (count or 0) >= 0 else "?"
    )


def push(workdir: Path, force: bool = False) -> None:
    """Push main to the remote in a single push.

    Batching is deliberately not attempted: GitHub indexes one push per
    repository well and subsequent pushes poorly, so splitting a history across
    several pushes makes the result worse, not better.
    """
    args = ["push", "--quiet"]
    if force:
        args.append("--force")
    args += [REMOTE, "main:refs/heads/main"]
    git(*args, cwd=workdir)


def ensure_private(config: Config, owner: str, info: dict, log=print) -> None:
    """Flip the repository to private when the config asks for it."""
    if not config.private or info.get("visibility", "").upper() == "PRIVATE":
        return
    log(f"  {owner}/{config.repo_name} is public; switching to private...")
    gh(
        "repo", "edit", f"{owner}/{config.repo_name}",
        "--visibility", "private",
        "--accept-visibility-change-consequences",
    )


def ensure_default_branch(config: Config, owner: str, info: dict, log=print) -> None:
    """A commit only counts when it sits on the default branch."""
    current = (info.get("defaultBranchRef") or {}).get("name")
    if current in (None, "main"):
        return
    log(f"  default branch was '{current}'; switching to 'main'...")
    gh("repo", "edit", f"{owner}/{config.repo_name}", "--default-branch", "main")


REMINDER = """
Two things left, both outside the API:

  1. If the repository is private, open
     https://github.com/settings/profile and, under "Contributions", tick
     "Include private contributions on my profile".
     Shortcut: the "Contribution settings" menu on your profile graph.
     Without it, commits in a private repository never show up.

  2. Indexing is asynchronous and takes a few minutes. The graph reads as
     empty until it finishes -- that is normal. Do not re-push while waiting:
     a second push is indexed far less reliably than the first.
"""
