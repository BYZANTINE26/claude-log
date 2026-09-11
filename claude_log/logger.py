"""Append-only JSONL session log: create/resume, read recent, append."""

import json
import os

from claude_log.paths import log_file_path


def initialize_or_resume(project_root: str, session_id: str, config: dict) -> str:
    """Ensure the session's log file exists and return its path.

    An existing file is left untouched (resume); a missing one is created
    empty. JSONL has no header line — every line is a data entry.
    """
    log_path = log_file_path(project_root, session_id, config)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    if not os.path.exists(log_path):
        open(log_path, "a", encoding="utf-8").close()
    return log_path


def get_recent_entries(log_file_path: str, count: int) -> list:
    """Return the last `count` entries, tolerant of a missing/empty file."""
    try:
        with open(log_file_path, "r", encoding="utf-8") as log_file:
            lines = log_file.readlines()
    except (FileNotFoundError, OSError):
        return []

    recent_entries = []
    for line in lines[-count:]:
        line = line.strip()
        if not line:
            continue
        try:
            recent_entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return recent_entries


def count_entries(log_file_path: str) -> int:
    """Number of lines already written, used to synthesize turn_id."""
    try:
        with open(log_file_path, "r", encoding="utf-8") as log_file:
            return sum(1 for line in log_file if line.strip())
    except (FileNotFoundError, OSError):
        return 0


def append_entry(log_file_path: str, entry: dict) -> None:
    """Append one JSON entry as a single line.

    A single write() call under one line's worth of data is atomic on
    POSIX for the single-writer case this MVP assumes (see BACKLOG.md for
    the multi-writer/locking limitation).
    """
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry) + "\n")


def build_entry(
    turn_id: str,
    timestamp: str,
    summary: str,
    refs: dict,
    context: dict | None,
    verbosity: str,
) -> dict:
    """Assemble a Slim or Rich log entry per SPEC.md's schema."""
    entry = {
        "turn_id": turn_id,
        "timestamp": timestamp,
        "summary": summary,
        "refs": refs,
    }
    if verbosity == "rich" and context is not None:
        entry["context"] = context
    return entry
