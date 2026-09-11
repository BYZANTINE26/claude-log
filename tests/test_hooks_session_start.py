"""Tests for the SessionStart hook: create/resume log, reset buffer."""

import json
import os

from claude_log.hooks.session_start import run
from claude_log.paths import log_file_path, turn_buffer_path
from tests.conftest import load_fixture, run_hook


def test_new_session_creates_log_and_buffer(project_root, config, monkeypatch):
    hook_input = load_fixture("session_start_new.json", project_root)
    run_hook(monkeypatch, run, hook_input)

    log_path = log_file_path(project_root, "test-session-new", config)
    buffer_path = turn_buffer_path(project_root, "test-session-new", config)
    assert os.path.exists(log_path)
    assert os.path.exists(buffer_path)


def test_resumed_session_appends_not_recreates(project_root, config, monkeypatch):
    from claude_log.logger import append_entry, initialize_or_resume

    log_path = initialize_or_resume(project_root, "test-session-resume", config)
    append_entry(log_path, {"turn_id": "test-session-resume:0", "summary": "prior"})

    hook_input = load_fixture("session_start_resume.json", project_root)
    run_hook(monkeypatch, run, hook_input)

    with open(log_path, "r", encoding="utf-8") as log_file:
        lines = [json.loads(line) for line in log_file if line.strip()]
    assert len(lines) == 1  # unchanged: SessionStart never truncates
    assert lines[0]["summary"] == "prior"


def test_session_start_resets_a_stale_buffer(project_root, config, monkeypatch):
    from claude_log.buffer import append_prompt

    buffer_path = turn_buffer_path(project_root, "test-session-new", config)
    append_prompt(buffer_path, "stale prompt from a crashed turn")

    hook_input = load_fixture("session_start_new.json", project_root)
    run_hook(monkeypatch, run, hook_input)

    with open(buffer_path, "r", encoding="utf-8") as buffer_file:
        buffer = json.load(buffer_file)
    assert buffer["prompt"] is None
