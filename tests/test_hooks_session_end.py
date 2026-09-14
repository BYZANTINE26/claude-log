from claude_log.buffer import start_turn
from claude_log.config import buffer_path
from claude_log.hooks.session_end import run
from claude_log.logger import get_recent_entries

from .conftest import run_hook


def test_sweeps_every_leftover_buffer_for_the_session(project_root, monkeypatch):
    start_turn(buffer_path(project_root, "sess1", "prompt1"), "never finished", None, {})
    start_turn(buffer_path(project_root, "sess1", "prompt2"), "also never finished", None, {})

    run_hook(monkeypatch, run, {"session_id": "sess1", "cwd": project_root, "reason": "other"})

    entries = get_recent_entries(project_root, "sess1", 10)
    assert len(entries) == 2
    assert all(entry["turn_lost"] for entry in entries)


def test_no_leftover_buffers_logs_nothing(project_root, monkeypatch):
    run_hook(monkeypatch, run, {"session_id": "sess1", "cwd": project_root, "reason": "other"})
    assert get_recent_entries(project_root, "sess1", 10) == []
