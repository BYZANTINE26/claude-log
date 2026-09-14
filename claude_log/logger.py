"""The append-only session log, and the context-reset window formula.

One JSONL file per session (`config.log_file_path`), one entry per turn.
A `/clear` marks a reset boundary in a small state file
(`config.state_path`) rather than in the log itself — see docs/adr/0007
for why the window formula derived from that state needs no separate
"current window size" counter.
"""

import contextlib
import json
import os

try:
    import fcntl  # POSIX
except ImportError:
    fcntl = None

try:
    import msvcrt  # Windows
except ImportError:
    msvcrt = None

from claude_log.config import log_file_path, project_log_dir, state_path

_EMPTY_STATE = {"reset_at_entry_index": None, "reingested_count": None}


@contextlib.contextmanager
def _locked(path: str):
    """Advisory OS-level exclusive lock on `<path>.lock`, serializing
    concurrent writers to `path` — two Claude Code sessions sharing a
    `session_id` can no longer interleave writes or race a
    read-modify-write and corrupt or lose an update (BACKLOG.md #16).

    ponytail: one lock per target file, held for the whole write — not
    fine-grained, but writes here are tiny and infrequent (once per
    turn), so contention is a non-issue at this scale.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(f"{path}.lock", "a+") as lock_file:
        if fcntl is not None:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
        elif msvcrt is not None:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(lock_file, fcntl.LOCK_UN)
            elif msvcrt is not None:
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)


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
    with _locked(log_path):
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
    `configured_window` entries, read with a backward seek so this never
    scans a large log's earlier turns just to discard them (see
    `BACKLOG.md #4`). Only a reset on record needs the log's total entry
    count (`_count_entries`), and even that skips JSON-parsing every line."""
    state = _read_state(project_root, session_id)

    reset_at = state["reset_at_entry_index"]
    if reset_at is None:
        window = configured_window
    else:
        total = _count_entries(project_root, session_id)
        entries_since_reset = max(total - reset_at, 0)
        reingested = state["reingested_count"] or 0
        window = min(configured_window, reingested + entries_since_reset)

    return _tail_entries(project_root, session_id, window) if window > 0 else []


def mark_context_reset(project_root: str, session_id: str) -> None:
    """Called from SessionStart on `source: "clear"` (docs/adr/0007)."""
    with _locked(state_path(project_root, session_id)):
        current_count = _count_entries(project_root, session_id)
        _write_state(
            project_root,
            session_id,
            {"reset_at_entry_index": current_count, "reingested_count": None},
        )


def record_reingestion(project_root: str, session_id: str, count: int) -> None:
    """Called from the `/claude-log-load [count]` skill."""
    with _locked(state_path(project_root, session_id)):
        state = _read_state(project_root, session_id)
        state["reingested_count"] = count
        _write_state(project_root, session_id, state)


def _count_entries(project_root: str, session_id: str) -> int:
    """Total entry count, without JSON-parsing a single line."""
    path = log_file_path(project_root, session_id)
    try:
        with open(path, "rb") as log_file:
            return sum(1 for line in log_file if line.strip())
    except (FileNotFoundError, OSError):
        return 0


def _tail_entries(project_root: str, session_id: str, count: int) -> list[dict]:
    """Last `count` entries, seeking backward from end-of-file in chunks
    instead of reading the whole log — cheap even for a large log when
    only a handful of recent turns are needed."""
    path = log_file_path(project_root, session_id)
    try:
        with open(path, "rb") as log_file:
            lines = _tail_lines(log_file, count)
    except (FileNotFoundError, OSError):
        return []
    return [json.loads(line) for line in lines]


def _tail_lines(file_obj, count: int) -> list[str]:
    chunk_size = 8192
    file_obj.seek(0, os.SEEK_END)
    position = file_obj.tell()
    chunks = []
    newlines_found = 0
    # A boundary chunk may cut a line in half, so read one extra newline's
    # worth before stopping, to guarantee `count` full lines are covered.
    while position > 0 and newlines_found <= count:
        read_size = min(chunk_size, position)
        position -= read_size
        file_obj.seek(position)
        chunk = file_obj.read(read_size)
        chunks.append(chunk)
        newlines_found += chunk.count(b"\n")
    data = b"".join(reversed(chunks))
    lines = [line.decode("utf-8") for line in data.split(b"\n") if line.strip()]
    return lines[-count:]


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
