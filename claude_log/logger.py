"""The append-only session log, and the context-reset window formula.

One JSONL file per session (`config.log_file_path`), one entry per turn.
A `/clear` marks a reset boundary in a small state file
(`config.state_path`) rather than in the log itself — see docs/adr/0007
for why the window formula derived from that state needs no separate
"current window size" counter.
"""

import json
import os

from claude_log.config import log_file_path, project_log_dir, state_path

_EMPTY_STATE = {"reset_at_entry_index": None, "reingested_count": None}


def initialize_or_resume(project_root: str, session_id: str) -> str:
    """Return this session's log path, ensuring its directory exists.

    Never creates or truncates the `.jsonl` file itself — a session with
    no completed turns yet should have no log file on disk, only a
    directory ready for the first `append_entry`.
    """
    path = log_file_path(project_root, session_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def append_entry(log_path: str, entry: dict) -> None:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry) + "\n")


def build_entry(
    turn_id: str,
    timestamp: str,
    summary: str | None,
    refs: dict,
    failure_flag: str | None = None,
) -> dict:
    """`failure_flag="summary_failed"` replaces `summary` with a marker
    (see docs/adr/0003) — never a fabricated fallback summary. `turn_lost`
    markers don't go through here; `buffer.sweep_orphaned` builds those
    directly, since a lost turn has no refs to attach."""
    entry = {"turn_id": turn_id, "timestamp": timestamp}
    if failure_flag == "summary_failed":
        entry["summary_failed"] = True
    else:
        entry["summary"] = summary
    entry["refs"] = refs
    return entry


def get_recent_entries(project_root: str, session_id: str, configured_window: int) -> list[dict]:
    """Last `min(configured_window, reingested_count + entries_since_reset)`
    entries. With no reset on record — plain `startup`, or a **resumed**
    session, which never gets a reset marker — this is just the last
    `configured_window` entries."""
    entries = _read_entries(project_root, session_id)
    state = _read_state(project_root, session_id)

    reset_at = state["reset_at_entry_index"]
    if reset_at is None:
        window = configured_window
    else:
        entries_since_reset = max(len(entries) - reset_at, 0)
        reingested = state["reingested_count"] or 0
        window = min(configured_window, reingested + entries_since_reset)

    return entries[-window:] if window > 0 else []


def mark_context_reset(project_root: str, session_id: str) -> None:
    """Called from SessionStart on `source: "clear"` (docs/adr/0007)."""
    current_count = len(_read_entries(project_root, session_id))
    _write_state(
        project_root, session_id, {"reset_at_entry_index": current_count, "reingested_count": None}
    )


def record_reingestion(project_root: str, session_id: str, count: int) -> None:
    """Called from the `/claude-log-load [count]` skill."""
    state = _read_state(project_root, session_id)
    state["reingested_count"] = count
    _write_state(project_root, session_id, state)


def _read_entries(project_root: str, session_id: str) -> list[dict]:
    path = log_file_path(project_root, session_id)
    try:
        with open(path, "r", encoding="utf-8") as log_file:
            return [json.loads(line) for line in log_file if line.strip()]
    except (FileNotFoundError, OSError):
        return []


def _read_state(project_root: str, session_id: str) -> dict:
    path = state_path(project_root, session_id)
    try:
        with open(path, "r", encoding="utf-8") as state_file:
            state = json.load(state_file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return dict(_EMPTY_STATE)
    return {**_EMPTY_STATE, **state}


def _write_state(project_root: str, session_id: str, state: dict) -> None:
    path = state_path(project_root, session_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_path = f"{path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as temp_file:
        json.dump(state, temp_file)
    os.replace(temp_path, path)
