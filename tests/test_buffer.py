"""Tests for claude_log.buffer: atomic per-turn scratch state."""

import os

from claude_log.buffer import (
    append_prompt,
    append_tool_call,
    read_and_clear,
    reset_buffer,
)


def test_reset_buffer_creates_empty_buffer(tmp_path):
    buffer_path = str(tmp_path / "buffer.json")
    reset_buffer(buffer_path)

    buffer = read_and_clear(buffer_path)
    assert buffer == {"prompt": None, "tool_calls": []}


def test_full_turn_round_trip(tmp_path):
    buffer_path = str(tmp_path / "buffer.json")
    reset_buffer(buffer_path)

    append_prompt(buffer_path, "fix the bug")
    append_tool_call(buffer_path, "Bash", "ran tests", {"command": "pytest"})
    append_tool_call(buffer_path, "Edit", "edited a file", {"file_path": "a.py"})

    buffer = read_and_clear(buffer_path)
    assert buffer["prompt"] == "fix the bug"
    assert len(buffer["tool_calls"]) == 2
    assert buffer["tool_calls"][0]["tool_name"] == "Bash"
    assert buffer["tool_calls"][1]["tool_name"] == "Edit"


def test_read_and_clear_resets_for_next_turn(tmp_path):
    buffer_path = str(tmp_path / "buffer.json")
    reset_buffer(buffer_path)
    append_prompt(buffer_path, "first turn")

    read_and_clear(buffer_path)
    second_buffer = read_and_clear(buffer_path)

    assert second_buffer == {"prompt": None, "tool_calls": []}


def test_no_tmp_file_survives_a_write(tmp_path):
    buffer_path = str(tmp_path / "buffer.json")
    reset_buffer(buffer_path)
    append_prompt(buffer_path, "hello")

    assert not os.path.exists(f"{buffer_path}.tmp")
    assert os.path.exists(buffer_path)


def test_read_missing_buffer_returns_empty(tmp_path):
    buffer_path = str(tmp_path / "does_not_exist.json")
    buffer = read_and_clear(buffer_path)
    assert buffer == {"prompt": None, "tool_calls": []}
