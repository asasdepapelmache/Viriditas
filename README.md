<h1 align="center">Viriditas</h1>

<p align="center">
  <em>Fill a GitHub contribution graph with backdated commits — from 1969 to today.</em>
</p>

<p align="center">
  <img alt="Python 3.11+" src="https://img.shields.io/badge/python-3.11%2B-blue">
  <img alt="Dependencies: none" src="https://img.shields.io/badge/dependencies-none-success">
  <img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-green">
  <img alt="Platforms" src="https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey">
</p>

<p align="center"><a href="README.pt-BR.md">🇧🇷 Leia em português</a></p>

---

```
Range:    1969-12-31 to 2026-09-29  (offset -0300)
Days:     20,727
Commits:  113,495
Done in 5.2s

     J    F   M   A   M    J   J   A    S   O    N   D
Sun   ░▒░░░▒░▒▒░░▒░▒░▒▒▒▒░▒░▒░▒▒░▒░▒▒░▒▒░▒░░▒▒░▒░▒▒░▒░░░░░
Mon   ▒▒▒▒▒▒░▓▒░▓▒▒▓▒▓▒░▒▒░▒▒▒▒▒▒▒░▒▒▒▒▒░▒▒▒▒▒▒▒░▒▒▒▒▒▓░▒░
Tue   ▒▒▒░▒▒▒▓▒▒▒▒▒░░▒░▒░▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░▒▒▒▒▒▒▒▒▒▒░▓▒░░░
Wed   ▒▒░▒▒▒░▒▓▒▒▓▒░░▒░░▒▒░▒▒▒▒░▒░▒▒░▒░▒▒░▒░░░▓░▒▒░░░▒▒▒░▒
Thu  ▒░▒▒▒▒▒▒▒░▒▒▓░▒▒▒▒░░▒░▒▒▒░▒▒░▒▒▒░▒▒▒▒▒▒▒▒▒▒▒▒░▒▒░▒▒▒▒
Fri  ▓▒▒▒▒░░▒▒▒▒▒░░░▒▒▒▒▒░▒▒░▒▓▓▒░▒▒░▒░▒▒▒▒▒░▒▒▒▒▒░▒▒▒▒▒░
Sat  ░▒▒░░▒▒▒░░▒░▒▒▒░▒░▒▒░▒▒░░░▒░░▒░░░░░▒░░░░▒▒▒▒░▒░░░▒▒░
     less ·░▒▓█ more
```

## What it does

Viriditas generates a Git repository whose history is spread across every day of
a range you choose — by default from **1969-12-31** to today, roughly 2,000
commits per year — and publishes it as a private repository so your contribution
graph is completely filled.

It is a cosmetic toy. It does not fake code review, pull requests, or anything
anyone could mistake for real work. The generated repository says what it is in
its own README, and a single command takes it all back.

**Why it is fast:** the history is written through `git fast-import`, not a loop
of `git commit`. Roughly 113,000 commits take about **5 seconds** and produce a
41 MB pack. The same work through `git commit` would take hours.

## Features

| | |
|---|---|
| 🗓️ **Reaches 1969** | The oldest day Git can express, via a negative UTC offset. See [the 1969 trick](#the-1969-trick). |
| 🎲 **Deterministic** | The same seed always produces the same graph. Change the seed, get a different texture. |
| 📊 **Terminal heatmap** | Preview any year as a GitHub-style grid before writing anything. |
| 🧮 **Shaped density** | Per-year targets within 5%, per-day floor and ceiling, lighter weekends. |
| 🔍 **Dry run** | `plan` writes nothing, and `--json` makes the schedule machine readable. |
| 🙈 **Hide** | `undo --hide` removes the graph from your profile without deleting a thing. |
| 🧹 **Clean** | `clean` drops the local build; `undo --delete` removes the remote too, with a typed confirmation. |
| ♻️ **Top up** | `topup` fills the days that passed since the last run. |
| 🛡️ **Guardrails** | Refuses non-empty targets, refuses forks, and only ever touches the repository named in your config. |
| 📦 **Zero dependencies** | Standard library only, on Linux, macOS and Windows. |

## Requirements

- **Python 3.11+** (uses `tomllib` from the standard library)
- **git**
- **[GitHub CLI](https://cli.github.com)** (`gh`), authenticated

```sh
gh auth login
```

No tokens are ever read, written, or stored by Viriditas: every API call is
delegated to `gh`.

## Install

```sh
git clone https://github.com/<you>/Viriditas.git
cd Viriditas
python -m viriditas --help
```

Or install it so the command is on your PATH:

```sh
pip install .
viriditas --help
```

## Quick start

```sh
viriditas init      # write viriditas.toml
viriditas check     # verify git, gh, login and config
viriditas plan      # dry run: totals, estimate, heatmap
viriditas run       # generate + push, with a confirmation
```

Then, **if the repository is private**, enable private contributions — there is
no API for this, so the tool can only remind you:

1. Open <https://github.com/settings/profile>
2. Under **Contributions**, tick **"Include private contributions on my profile"**

Indexing is asynchronous and takes a few minutes. The graph reads as empty until
it finishes; that is normal. **Do not re-push while waiting** — see below.

## Commands

| Command | What it does |
|---|---|
| `viriditas init` | Write a starter `viriditas.toml` (`--force` overwrites) |
| `viriditas check` | Verify Python, `git`, `gh`, authentication and the config |
| `viriditas plan` | Dry run: totals per year, time estimate, ASCII heatmap (`--year 1987`, `--json`) |
| `viriditas generate` | Build the local repository via `git fast-import` (`--force` rebuilds) |
| `viriditas push` | Create the repository and push (refuses a non-empty target) |
| `viriditas run` | `check` → `plan` → confirm → `generate` → `push` |
| `viriditas status` | Local and remote state, plus the reminders that apply |
| `viriditas topup` | Generate and push only the days missing since the last commit |
| `viriditas clean` | Delete the local build folder; the remote is untouched |
| `viriditas undo --hide` | Print how to disappear from the graph without deleting anything |
| `viriditas undo --delete` | Delete the remote repository and the local folder, with a typed confirmation |

Every command accepts `--config path/to/viriditas.toml`.

## Configuration

```toml
[github]
repo_name = "contribution-canvas"  # MUST be empty or not exist yet
private = true
name = "auto"                      # "auto" = the authenticated account
email = "auto"                      # "auto" = that account's noreply address

[range]
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
```

`workdir` must be a native path. On Windows use `./build/...` or `C:/...`; an
MSYS-style path like `/c/Users/...` will not resolve.

## ⚠️ The target repository must be empty

This is the one thing that silently ruins the result, and it is not documented
anywhere by GitHub.

**GitHub only indexes a full history on the first push to a freshly created
repository.** Pushing on top of an existing history is indexed partially, or not
at all — even with `--force`, even though the push succeeds and every commit is
verifiably present on the remote.

Measured across six runs, reading the graph back through the GraphQL API:

| Commits pushed | Repository state | Counted on the graph |
|---|---|---|
| 5 | first push, fresh repository | **5** ✅ |
| 1,500 | first push, fresh repository | **1,500** ✅ |
| 113,495 | first push, fresh repository | **113,495** ✅ |
| 1,500 (as 3 pushes of 500) | existing history | 500 |
| 20,000 (one push) | existing history | 0 |
| 113,495 (`--force`) | existing history (23 commits) | 1,000 |

What follows from that:

- **Volume is not the limit.** 113,495 commits in a single push were all
  counted, and the push took 8.5 seconds.
- **Batching makes it worse.** Three pushes of 500 counted 500, not 1,500. Only
  the first one landed. Viriditas therefore pushes once and never splits.
- **Indexing lags by minutes.** Roughly six in testing. Zero on the graph right
  after a push means "not yet", not "failed". Re-pushing restarts you on the
  unreliable path.
- **So `push` refuses a non-empty target.** `--force` overrides it and warns,
  but the graph will most likely stay incomplete.

If you already pushed onto a dirty repository, point `repo_name` at a new one —
or delete and recreate it — and push again as its first push.

## How GitHub counts contributions

Viriditas respects all of these, and `check`/`status` surface the ones it cannot
enforce:

- The commit must be on the repository's **default branch** (`main`).
- The author email must be **linked to the account**. With `email = "auto"` the
  tool uses `<id>+<login>@users.noreply.github.com`, read from `gh api user`,
  which always is.
- The repository must **not be a fork**. `push` refuses forks outright.
- A private repository needs **"Include private contributions on my profile"**.
- The day a commit lands on is computed from the **UTC offset stored in the
  commit itself**, not from UTC.

## The 1969 trick

Git stores dates as Unix timestamps, so `1970-01-01 00:00 UTC` is the floor. To
show **1969** on the graph you write a commit just after the epoch with a
negative offset: the instant is post-epoch, but the commit's *local* date is
1969-12-31.

| timestamp | offset | local date of the commit |
|---|---|---|
| `3600` | `-0300` | `1969-12-31 22:00:00` |

`git fast-import --date-format=raw` accepts this without complaint. The object
literally stores `author ... 3600 -0300`, `git fsck` passes clean, and `git
clone` transfers it normally. Timestamp `0` is avoided on purpose — some tools
read it as "no date" — so the floor used is `1`.

With offset `-0300`, 1969-12-31 only exists between timestamps `1` and `10799`,
which is 21:00 to 23:59 local time. `day_window()` clamps each day to that floor
automatically, and that is why profiles like this show 1969 as a single day.

### Side effect: your local `git log` cannot format that date

Any `git log` that *formats* the date aborts on that commit:

```console
$ git log -1 --date=iso
fatal: Timestamp before Unix epoch: 3600 -300
```

This is a limitation of the local `git` renderer only — not of the object, and
not of GitHub. Inspect it with `--date=raw` instead:

```sh
git log --reverse --date=raw --format='%ad %s' | head -3
```

Viriditas does exactly that internally (`generator.raw_bounds`) and converts to
a readable date in Python (`generator.raw_to_display`).

## Undoing it

Two ways, gentlest first:

```sh
viriditas undo --hide     # changes nothing; tells you how to vanish from the graph
viriditas clean           # deletes the local build only
viriditas undo --delete   # deletes the remote repository and the local folder
```

- **`--hide`** touches nothing. It prints how to untick *"Include private
  contributions on my profile"*, which takes the graph back to public activity
  only and is reversible whenever you want.
- **`--delete`** is permanent. It needs the `delete_repo` scope
  (`gh auth refresh -h github.com -s delete_repo`), shows the repository and its
  commit count, and only proceeds once you **type the repository name**.
  Safeguard: it will only ever delete the repository named in your config file.

## Project layout

```
viriditas/
  cli.py          # argparse, commands, output
  config.py       # load and validate the TOML config
  schedule.py     # how many commits per day (deterministic, pure)
  preview.py      # ASCII heatmap with a legacy-terminal fallback
  generator.py    # the fast-import stream and the local repository
  publisher.py    # create the repository and push
  undo.py         # hide, clean, delete
  github.py       # thin wrappers over git and gh
tests/
  test_schedule.py
```

## Tests

```sh
python tests/test_schedule.py    # no pytest needed
python -m pytest                 # if you have it
```

They cover determinism per seed, per-day floor and ceiling, yearly totals within
5%, leap and non-leap years, no missing days, prorated partial years, lighter
weekends, year-independence from the range, config rejection paths, heatmap
geometry and the legacy-terminal fallback, plus the timestamp arithmetic —
including the 1969 window and that every generated timestamp lands on the day it
was meant for.

## FAQ

**Does this get me banned?**
Nothing here violates the GitHub Terms of Service: they are ordinary commits in
your own repository, authored by you. It is cosmetic, and anyone who looks at
the repository sees immediately what it is. Do not present it as real work.

**Will people see the repository?**
Not if it is private. The graph shows the *count*, and a private contribution
renders as a filled square with no link. Making it public would put a repository
of 113,000 meaningless commits on your profile — `private = true` is the default
for a reason.

**Can I change the shape?**
Change `seed` for a different texture, `target_per_year` for overall intensity,
`min_per_day` / `max_per_day` for contrast, and `weekend_factor` for the weekly
rhythm. Run `viriditas plan --year <year>` to see the result before generating.

**Why the name?**
*Viriditas* is Hildegard of Bingen's word for the greening force of living
things. It seemed right for a tool whose entire output is green squares.

## License

MIT — see [LICENSE](LICENSE).
