"""Tests for claude_log.paths: log and buffer path resolution."""

from claude_log.paths import log_file_path, turn_buffer_path


def test_log_file_path(project_root, config):
    path = log_file_path(project_root, "session-1", config)
    assert path.endswith(".claude/logs/session_session-1.jsonl")


def test_turn_buffer_path(project_root, config):
    path = turn_buffer_path(project_root, "session-1", config)
    assert path.endswith(".claude/logs/.buffers/session_session-1.json")
