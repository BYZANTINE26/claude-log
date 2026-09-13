"""Git-based file-touch tracking for a turn (see docs/adr/0004).

Rather than tracking individual tool calls, a turn's touched files are
derived by snapshotting git state at `UserPromptSubmit` and again at
`Stop`, then diffing the two snapshots: committed changes come from a
plain commit-to-commit diff, uncommitted/untracked changes come from
comparing content hashes of whatever `git status --porcelain` reports
dirty at each end. Hashing (not just listing) the dirty set is what lets
a pre-existing dirty file the turn never touched be correctly excluded.
"""

import os
import subprocess

# Used for a path that's dirty but not a plain file `git hash-object`
# can hash: deleted, or a directory (e.g. a nested repo/submodule).
_DELETED_SENTINEL = "<deleted>"


def snapshot_git_state(project_root: str) -> dict:
    """`{"commit": str | None, "dirty": {path: content_hash}}`.

    `commit` is None outside a git repo or before the first commit.
    `dirty` covers both tracked-uncommitted and untracked paths — a
    plain `git status --porcelain` listing, each hashed with
    `git hash-object` so two snapshots of the same path can be compared
    for an actual content change, not just "was dirty".
    """
    commit = _run(["git", "rev-parse", "HEAD"], project_root) or None
    dirty_paths = _dirty_paths(project_root)
    return {"commit": commit, "dirty": _hash_paths(dirty_paths, project_root)}


def files_touched(before: dict, after: dict, project_root: str) -> list[str]:
    """Union of committed changes (`before["commit"]..after["commit"]`)
    and paths whose dirty-hash changed or newly appeared. A path whose
    hash is unchanged between snapshots was dirty before the turn and
    stayed untouched by it, so it's correctly excluded."""
    touched = set()

    if before["commit"] and after["commit"]:
        touched.update(
            _run(
                ["git", "diff", "--name-only", f"{before['commit']}..{after['commit']}"],
                project_root,
            ).splitlines()
            if before["commit"] != after["commit"]
            else []
        )

    for path, content_hash in after["dirty"].items():
        if before["dirty"].get(path) != content_hash:
            touched.add(path)

    return sorted(touched)


def _dirty_paths(project_root: str) -> list[str]:
    # --untracked-files=all: without it, git folds an entirely-untracked
    # directory into one "?? somedir/" line instead of listing its files
    # individually. A directory path surviving into _hash_paths makes the
    # single batched `git hash-object` call fail outright (it can't hash
    # a directory), which used to empty the whole hash map for every
    # path in that batch, not just the directory one — found live via a
    # real test run once `.claude-log/.state/` existed as an untracked
    # directory in a test project.
    output = _run(["git", "status", "--porcelain", "--untracked-files=all"], project_root)
    if not output:
        return []
    paths = []
    for line in output.splitlines():
        path = line[3:].strip()
        if " -> " in path:  # rename: "old -> new", keep the new path
            path = path.split(" -> ", 1)[1]
        paths.append(path.strip('"'))
    return paths


def _hash_paths(paths: list[str], project_root: str) -> dict:
    """`git hash-object` can't hash a directory — one such path in a
    batched call fails the whole call, silently zeroing every other
    path's hash too (`_run` swallows the non-zero exit as ""). Skipping
    directories here is a second guard on top of `--untracked-files=all`
    in `_dirty_paths`, for cases that still surface one anyway (e.g. a
    nested git repo/submodule, which git status never expands)."""
    if not paths:
        return {}
    existing = [
        path
        for path in paths
        if os.path.isfile(os.path.join(project_root, path))
    ]
    hashes = {path: _DELETED_SENTINEL for path in paths if path not in existing}
    if existing:
        output = _run(["git", "hash-object", *existing], project_root)
        hashes.update(zip(existing, output.splitlines()))
    return hashes


def _run(command: list[str], project_root: str) -> str:
    """Run a git command, returning stripped stdout or "" on any
    failure (not a git repo, no commits yet, git not installed)."""
    try:
        result = subprocess.run(
            command, cwd=project_root, capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if result.returncode != 0:
        return ""
    # rstrip only: `git status --porcelain`'s leading status-code column
    # can start with a meaningful space (e.g. " D file" = unstaged
    # delete), which a two-sided strip() would corrupt on the first line.
    return result.stdout.rstrip("\n")
