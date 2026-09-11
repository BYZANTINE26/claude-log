"""Resolve on-disk paths for a session's log file and turn buffer."""

import os


def log_file_path(project_root: str, session_id: str, config: dict) -> str:
    """Path to the session's append-only JSONL log."""
    log_directory = os.path.join(project_root, config["log_directory"])
    return os.path.join(log_directory, f"session_{session_id}.jsonl")


def turn_buffer_path(project_root: str, session_id: str, config: dict) -> str:
    """Path to the session's per-turn scratch buffer.

    Kept in a `.buffers/` subdirectory of the log directory so it never
    matches a `*.jsonl` glob over session logs.
    """
    buffers_directory = os.path.join(
        project_root, config["log_directory"], ".buffers"
    )
    return os.path.join(buffers_directory, f"session_{session_id}.json")
