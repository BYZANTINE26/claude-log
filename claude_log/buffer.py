"""Per-turn scratch buffer, accumulated across hook invocations.

Claude Code hooks fire as separate OS processes with no shared memory, so
a turn's prompt and tool calls must be persisted between UserPromptSubmit,
PostToolUse, and Stop. Every mutation here is a full read-modify-write,
written to a temp file and then atomically renamed into place via
os.replace, so a process killed mid-write never leaves a half-written
buffer behind.
"""

import json
import os

EMPTY_BUFFER = {"prompt": None, "tool_calls": []}


def reset_buffer(buffer_path: str) -> None:
    """Overwrite the buffer with an empty turn, creating it if needed."""
    _write_buffer(buffer_path, dict(EMPTY_BUFFER))


def append_prompt(buffer_path: str, prompt_text: str) -> None:
    """Record the user's prompt for the in-progress turn."""
    buffer = _read_buffer(buffer_path)
    buffer["prompt"] = prompt_text
    _write_buffer(buffer_path, buffer)


def append_tool_call(
    buffer_path: str, tool_name: str, result_summary: str, tool_input: dict
) -> None:
    """Record one tool call for the in-progress turn."""
    buffer = _read_buffer(buffer_path)
    buffer["tool_calls"].append(
        {
            "tool_name": tool_name,
            "result_summary": result_summary,
            "tool_input": tool_input,
        }
    )
    _write_buffer(buffer_path, buffer)


def read_and_clear(buffer_path: str) -> dict:
    """Return the buffer's contents and reset it for the next turn."""
    buffer = _read_buffer(buffer_path)
    reset_buffer(buffer_path)
    return buffer


def _read_buffer(buffer_path: str) -> dict:
    try:
        with open(buffer_path, "r", encoding="utf-8") as buffer_file:
            return json.load(buffer_file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return dict(EMPTY_BUFFER)


def _write_buffer(buffer_path: str, buffer: dict) -> None:
    os.makedirs(os.path.dirname(buffer_path), exist_ok=True)
    temp_path = f"{buffer_path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as temp_file:
        json.dump(buffer, temp_file)
    os.replace(temp_path, buffer_path)
