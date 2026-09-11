"""Tests for the PostToolUse hook: append one tool call to the buffer."""

import json

from claude_log.hooks.post_tool_use import run as run_post_tool_use
from claude_log.hooks.session_start import run as run_session_start
from claude_log.paths import turn_buffer_path
from tests.conftest import load_fixture, run_hook


def test_two_tool_calls_both_land_in_the_buffer(project_root, config, monkeypatch):
    run_hook(
        monkeypatch, run_session_start,
        load_fixture("session_start_new.json", project_root),
    )
    run_hook(
        monkeypatch, run_post_tool_use,
        load_fixture("post_tool_use_bash.json", project_root),
    )
    run_hook(
        monkeypatch, run_post_tool_use,
        load_fixture("post_tool_use_edit.json", project_root),
    )

    buffer_path = turn_buffer_path(project_root, "test-session-new", config)
    with open(buffer_path, "r", encoding="utf-8") as buffer_file:
        buffer = json.load(buffer_file)

    tool_names = [call["tool_name"] for call in buffer["tool_calls"]]
    assert tool_names == ["Bash", "Edit"]


def test_long_string_response_is_truncated(project_root, config, monkeypatch):
    long_response = "x" * 500
    hook_input = load_fixture("post_tool_use_bash.json", project_root)
    hook_input["tool_response"] = long_response

    run_hook(
        monkeypatch, run_session_start,
        load_fixture("session_start_new.json", project_root),
    )
    run_hook(monkeypatch, run_post_tool_use, hook_input)

    buffer_path = turn_buffer_path(project_root, "test-session-new", config)
    with open(buffer_path, "r", encoding="utf-8") as buffer_file:
        buffer = json.load(buffer_file)
    assert len(buffer["tool_calls"][0]["result_summary"]) < len(long_response)


def test_dict_response_describes_without_dumping_full_content(
    project_root, config, monkeypatch
):
    """Edit/Write tool_response carries the whole file diff as a dict —
    the buffer must keep only a short descriptor, never that full content."""
    hook_input = load_fixture("post_tool_use_edit.json", project_root)
    hook_input["tool_response"] = {
        "type": "update",
        "filePath": "claude_log/logger.py",
        "oldString": "x" * 5000,
        "newString": "y" * 5000,
    }

    run_hook(
        monkeypatch, run_session_start,
        load_fixture("session_start_new.json", project_root),
    )
    run_hook(monkeypatch, run_post_tool_use, hook_input)

    buffer_path = turn_buffer_path(project_root, "test-session-new", config)
    with open(buffer_path, "r", encoding="utf-8") as buffer_file:
        buffer = json.load(buffer_file)
    result_summary = buffer["tool_calls"][0]["result_summary"]
    assert "update" in result_summary
    assert "claude_log/logger.py" in result_summary
    assert "x" * 100 not in result_summary
