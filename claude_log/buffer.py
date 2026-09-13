"""Per-turn scratch buffer, accumulated across separate hook processes.

Claude Code hooks share no memory (see docs/adr/0006), so a turn's
prompt, git-start snapshot, and assistant message text must persist
between UserPromptSubmit, MessageDisplay, and Stop. Buffers are keyed by
`<session_id>__<prompt_id>.json` (config.buffer_path) — one disposable
file per turn, deleted once Stop reads it, so an interrupted or
overlapping turn can never corrupt another turn's data.

Every mutation is a full read-modify-write via a temp file + os.replace,
so a process killed mid-write never leaves a half-written buffer behind.
"""

import json
import os
from datetime import datetime, timezone

from claude_log.config import project_log_dir

_EMPTY_BUFFER = {
    "prompt": None,
    "assistant_messages": [],
    "pending_message_id": None,
    "pending_message_text": "",
    "commit_before": None,
    "dirty_before": {},
}


def start_turn(
    buffer_path: str, prompt_text: str, commit_before: str | None, dirty_before: dict
) -> None:
    """Create a fresh buffer for a new turn (called from UserPromptSubmit)."""
    buffer = dict(_EMPTY_BUFFER)
    buffer["prompt"] = prompt_text
    buffer["commit_before"] = commit_before
    buffer["dirty_before"] = dirty_before
    _write_buffer(buffer_path, buffer)


def append_message_delta(
    buffer_path: str, message_id: str, delta_text: str, final: bool
) -> None:
    """Accumulate one MessageDisplay batch (see docs/adr/0005).

    `delta` arrives incrementally per `message_id` in interactive
    sessions; a new `message_id` starts a fresh accumulation, and
    `final: true` moves the completed text into `assistant_messages`.
    """
    buffer = _read_buffer(buffer_path)
    if buffer["pending_message_id"] != message_id:
        buffer["pending_message_id"] = message_id
        buffer["pending_message_text"] = ""
    buffer["pending_message_text"] += delta_text
    if final:
        buffer["assistant_messages"].append(buffer["pending_message_text"])
        buffer["pending_message_id"] = None
        buffer["pending_message_text"] = ""
    _write_buffer(buffer_path, buffer)


def read_and_clear(buffer_path: str) -> dict:
    """Return the buffer's contents and delete it (called from Stop)."""
    buffer = _read_buffer(buffer_path)
    _delete(buffer_path)
    return buffer


def sweep_orphaned(project_root: str, session_id: str, keep_prompt_id: str) -> list[dict]:
    """Delete any other turn's leftover buffer for this session, and
    return a `turn_lost` marker entry per one found (see docs/adr/0006).

    Called from UserPromptSubmit (before starting the new turn) and
    SessionEnd — a leftover file means its turn's Stop never ran, so its
    content is intentionally discarded, never fabricated or merged into
    another turn.
    """
    buffers_dir = os.path.join(project_log_dir(project_root), ".buffers")
    prefix = f"{session_id}__"
    keep_name = f"{prefix}{keep_prompt_id}.json"

    markers = []
    if not os.path.isdir(buffers_dir):
        return markers
    for filename in os.listdir(buffers_dir):
        if not filename.startswith(prefix) or filename == keep_name:
            continue
        orphaned_prompt_id = filename[len(prefix) : -len(".json")]
        markers.append(
            {
                "turn_id": orphaned_prompt_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "turn_lost": True,
            }
        )
        _delete(os.path.join(buffers_dir, filename))
    return markers


def _read_buffer(buffer_path: str) -> dict:
    try:
        with open(buffer_path, "r", encoding="utf-8") as buffer_file:
            return json.load(buffer_file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return dict(_EMPTY_BUFFER)


def _write_buffer(buffer_path: str, buffer: dict) -> None:
    os.makedirs(os.path.dirname(buffer_path), exist_ok=True)
    temp_path = f"{buffer_path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as temp_file:
        json.dump(buffer, temp_file)
    os.replace(temp_path, buffer_path)


def _delete(buffer_path: str) -> None:
    try:
        os.remove(buffer_path)
    except FileNotFoundError:
        pass
