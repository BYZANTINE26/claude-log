"""Tests for the UserPromptSubmit hook: record the prompt into the buffer."""

import json

from claude_log.hooks.session_start import run as run_session_start
from claude_log.hooks.user_prompt_submit import run as run_user_prompt_submit
from claude_log.paths import turn_buffer_path
from tests.conftest import load_fixture, run_hook


def test_prompt_is_recorded_into_the_buffer(project_root, config, monkeypatch):
    run_hook(
        monkeypatch, run_session_start,
        load_fixture("session_start_new.json", project_root),
    )
    run_hook(
        monkeypatch, run_user_prompt_submit,
        load_fixture("user_prompt_submit.json", project_root),
    )

    buffer_path = turn_buffer_path(project_root, "test-session-new", config)
    with open(buffer_path, "r", encoding="utf-8") as buffer_file:
        buffer = json.load(buffer_file)
    assert buffer["prompt"] == "please fix the failing test"
