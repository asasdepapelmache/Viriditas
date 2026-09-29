"""Undo, from the gentlest option to the permanent one."""

from __future__ import annotations

from .config import Config
from .generator import remove_workdir
from .github import ToolError, gh, git, repo_info, token_scopes

HIDE_STEPS = """
How to hide the commits without deleting anything (reversible at any time):

  1. Open https://github.com/settings/profile
  2. Under "Contributions", UNTICK
     "Include private contributions on my profile".
  3. Save. Your graph goes back to showing public activity only.

Nothing was changed just now: not the remote repository, not the local folder.
Tick the option again to bring the graph back.

This only works while the repository is private. A public repository has to be
made private, deleted, or archived instead.
"""


class UndoError(Exception):
    """Undo failed, with a message meant for the user."""


def hide(log=print) -> None:
    log(HIDE_STEPS)


def clean(config: Config, log=print) -> bool:
    """Delete the local working directory. The remote is never touched."""
    if remove_workdir(config.workdir):
        log(f"  removed {config.workdir}")
        return True
    log(f"  {config.workdir} does not exist; nothing to clean.")
    return False


def delete(config: Config, owner: str, confirm, log=print) -> None:
    """Delete the remote repository and the local folder.

    `confirm` is called with the expected repository name and must return what
    the user typed. Safeguard: only the repository named in the config file can
    ever be deleted.
    """
    target = f"{owner}/{config.repo_name}"

    scopes = token_scopes()
    if scopes and "delete_repo" not in scopes:
        raise UndoError(
            "the gh token is missing the `delete_repo` scope. Run:\n\n"
            "  gh auth refresh -h github.com -s delete_repo\n\n"
            "then try again."
        )

    info = repo_info(owner, config.repo_name)
    if info is None:
        log(f"{target} does not exist on GitHub; nothing to delete there.")
    else:
        count = _remote_count(config)
        log("\nThis will PERMANENTLY delete the remote repository:")
        log(f"  {info.get('url') or target}")
        log(
            f"  visibility: {info.get('visibility', '?')}  |  "
            f"commits: {count if count is not None else '?'}"
        )
        log("\nThere is no undo. Type the repository name to confirm.")

        if confirm(config.repo_name).strip() != config.repo_name:
            raise UndoError("name did not match; nothing was deleted.")

        gh("repo", "delete", target, "--yes")
        log(f"  deleted remote repository {target}")

    clean(config, log=log)
    log(
        "\nDone. The contribution graph usually drops those days immediately, "
        "but allow a little time."
    )


def _remote_count(config: Config) -> int | None:
    """Count the remote main branch, when a local clone is around to ask."""
    if not config.workdir.exists():
        return None
    try:
        git("fetch", "--quiet", "origin", "main", cwd=config.workdir)
        return int(
            git("rev-list", "--count", "FETCH_HEAD", cwd=config.workdir).strip()
        )
    except (ToolError, ValueError):
        return None
