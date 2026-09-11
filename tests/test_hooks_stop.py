"""Tests for the Stop hook: summarize once, append one log entry."""

from claude_log.hooks.post_tool_use import run as run_post_tool_use
from claude_log.hooks.session_start import run as run_session_start
from claude_log.hooks.stop import run as run_stop
from claude_log.hooks.user_prompt_submit import run as run_user_prompt_submit
from claude_log.logger import get_recent_entries
from claude_log.paths import log_file_path
from tests.conftest import load_fixture, run_hook


def _run_full_turn(project_root, monkeypatch):
    run_hook(
        monkeypatch, run_session_start,
        load_fixture("session_start_new.json", project_root),
    )
    run_hook(
        monkeypatch, run_user_prompt_submit,
        load_fixture("user_prompt_submit.json", project_root),
    )
    run_hook(
        monkeypatch, run_post_tool_use,
        load_fixture("post_tool_use_bash.json", project_root),
    )
    run_hook(
        monkeypatch, run_post_tool_use,
        load_fixture("post_tool_use_edit.json", project_root),
    )
    run_hook(monkeypatch, run_stop, load_fixture("stop.json", project_root))


def test_full_turn_yields_exactly_one_log_line(project_root, config, monkeypatch):
    _run_full_turn(project_root, monkeypatch)

    log_path = log_file_path(project_root, "test-session-new", config)
    entries = get_recent_entries(log_path, 10)
    assert len(entries) == 1

    entry = entries[0]
    assert entry["refs"]["tools"] == ["Bash", "Edit"]
    assert "claude_log/logger.py" in entry["refs"]["files"]


def test_empty_turn_writes_nothing(project_root, config, monkeypatch):
    run_hook(
        monkeypatch, run_session_start,
        load_fixture("session_start_new.json", project_root),
    )
    run_hook(monkeypatch, run_stop, load_fixture("stop.json", project_root))

    log_path = log_file_path(project_root, "test-session-new", config)
    assert get_recent_entries(log_path, 10) == []


def test_second_turn_appends_a_second_line(project_root, config, monkeypatch):
    _run_full_turn(project_root, monkeypatch)
    _run_full_turn(project_root, monkeypatch)

    log_path = log_file_path(project_root, "test-session-new", config)
    entries = get_recent_entries(log_path, 10)
    assert len(entries) == 2
    assert entries[0]["turn_id"] != entries[1]["turn_id"]
