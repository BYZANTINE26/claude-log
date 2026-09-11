"""Deep-dive metadata for a log entry: commit hash and touched files."""

import subprocess

_FILE_PATH_TOOLS = {"Edit", "Write", "NotebookEdit"}


def current_commit_hash(project_root: str) -> str | None:
    """Return `git rev-parse HEAD`, or None if not a git repo / no commits."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if result.returncode != 0:
        return None
    return result.stdout.strip()


def files_touched(tool_calls: list) -> list:
    """Dedup, order-preserving list of file paths touched by edit tools."""
    seen_paths = []
    for call in tool_calls:
        if call.get("tool_name") not in _FILE_PATH_TOOLS:
            continue
        file_path = call.get("tool_input", {}).get("file_path")
        if file_path and file_path not in seen_paths:
            seen_paths.append(file_path)
    return seen_paths
