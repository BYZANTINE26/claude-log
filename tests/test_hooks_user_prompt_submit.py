import json
import os

from claude_log.buffer import start_turn
from claude_log.config import buffer_path
from claude_log.hooks.user_prompt_submit import run

from .conftest import run_hook


def test_starts_a_fresh_buffer(project_root, monkeypatch, capsys):
    run_hook(
        monkeypatch,
        run,
        {"session_id": "sess1", "cwd": project_root, "prompt_id": "prompt1", "prompt": "add X"},
    )

    path = buffer_path(project_root, "sess1", "prompt1")
    with open(path) as buffer_file:
        buffer = json.load(buffer_file)
    assert buffer["prompt"] == "add X"
    assert capsys.readouterr().out == ""  # no lost turns -> no systemMessage


def test_sweeps_orphaned_buffer_from_previous_turn(project_root, monkeypatch, capsys):
    stale_path = buffer_path(project_root, "sess1", "old-prompt")
    start_turn(stale_path, "old, never finished", None, {})

    run_hook(
        monkeypatch,
        run,
        {"session_id": "sess1", "cwd": project_root, "prompt_id": "new-prompt", "prompt": "add Y"},
    )

    assert not os.path.exists(stale_path)
    output = capsys.readouterr().out
    assert "lost" in json.loads(output)["systemMessage"]


def test_missing_git_repo_still_starts_turn(project_root, monkeypatch):
    """No git repo: commit/dirty snapshot degrade gracefully."""
    run_hook(
        monkeypatch,
        run,
        {"session_id": "sess1", "cwd": project_root, "prompt_id": "prompt1", "prompt": "add X"},
    )
    path = buffer_path(project_root, "sess1", "prompt1")
    with open(path) as buffer_file:
        buffer = json.load(buffer_file)
    assert buffer["commit_before"] is None
