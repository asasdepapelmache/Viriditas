"""Thin wrappers around the `git` and `gh` command line tools.

Nothing here stores a token: authentication is always delegated to `gh`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Windows installers do not always refresh PATH for the running shell.
GH_FALLBACKS = [
    r"C:\Program Files\GitHub CLI\gh.exe",
    r"C:\Program Files (x86)\GitHub CLI\gh.exe",
    r"%LOCALAPPDATA%\GitHubCLI\bin\gh.exe",
]
GIT_FALLBACKS = [
    r"C:\Program Files\Git\cmd\git.exe",
    r"C:\Program Files\Git\mingw64\bin\git.exe",
]

MIN_PYTHON = (3, 11)


class ToolError(Exception):
    """A `git` or `gh` call failed, with a message meant for the user."""


def _resolve(name: str, fallbacks: list[str]) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    for candidate in fallbacks:
        expanded = os.path.expandvars(candidate)
        if Path(expanded).exists():
            return expanded
    return None


def gh_path() -> str | None:
    return _resolve("gh", GH_FALLBACKS)


def git_path() -> str | None:
    return _resolve("git", GIT_FALLBACKS)


def _run(executable: str, args: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(
        [executable, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        **kwargs,
    )


def gh(*args: str, check: bool = True) -> str:
    """Run `gh` and return stdout."""
    executable = gh_path()
    if executable is None:
        raise ToolError(
            "GitHub CLI (gh) not found. Install it from https://cli.github.com "
            "and open a new terminal."
        )
    result = _run(executable, list(args))
    if check and result.returncode != 0:
        raise ToolError(
            f"`gh {' '.join(args)}` failed with exit code {result.returncode}:\n"
            f"{(result.stderr or result.stdout).strip()}"
        )
    return result.stdout


def gh_json(*args: str):
    return json.loads(gh(*args) or "null")


def git(*args: str, cwd: str | Path | None = None, check: bool = True) -> str:
    """Run `git` and return stdout."""
    executable = git_path()
    if executable is None:
        raise ToolError("git not found on PATH.")
    result = _run(executable, list(args), cwd=str(cwd) if cwd else None)
    if check and result.returncode != 0:
        raise ToolError(
            f"`git {' '.join(args)}` failed with exit code {result.returncode}:\n"
            f"{(result.stderr or result.stdout).strip()}"
        )
    return result.stdout


def auth_status() -> tuple[bool, str]:
    """(authenticated, human readable detail)."""
    executable = gh_path()
    if executable is None:
        return False, "gh is not installed"
    result = _run(executable, ["auth", "status"])
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def token_scopes() -> list[str]:
    """OAuth scopes on the current gh token, empty when unknown."""
    authenticated, detail = auth_status()
    if not authenticated:
        return []
    for line in detail.splitlines():
        if "Token scopes:" in line:
            raw = line.split("Token scopes:", 1)[1]
            return [item.strip().strip("'\"") for item in raw.split(",") if item.strip()]
    return []


def current_user() -> dict:
    """Login, numeric id, display name and the account's noreply address.

    The noreply address is always linked to the account, which is what makes a
    commit count towards the contribution graph.
    """
    data = gh_json("api", "user")
    login = data["login"]
    user_id = data["id"]
    return {
        "login": login,
        "id": user_id,
        "name": data.get("name") or login,
        "noreply_email": f"{user_id}+{login}@users.noreply.github.com",
    }


def repo_info(owner: str, repo: str) -> dict | None:
    """Repository metadata, or None when it does not exist."""
    executable = gh_path()
    if executable is None:
        raise ToolError("GitHub CLI (gh) not found.")
    result = _run(
        executable,
        [
            "repo", "view", f"{owner}/{repo}",
            "--json", "name,visibility,isFork,defaultBranchRef,isEmpty,url",
        ],
    )
    if result.returncode != 0:
        combined = (result.stderr + result.stdout).lower()
        if "could not resolve" in combined or "not found" in combined:
            return None
        raise ToolError(
            f"could not read {owner}/{repo}:\n"
            f"{(result.stderr or result.stdout).strip()}"
        )
    return json.loads(result.stdout)


def python_version() -> tuple[bool, str]:
    info = sys.version_info
    version = f"{info.major}.{info.minor}.{info.micro}"
    return info >= MIN_PYTHON, version
