import json

from claude_log.buffer import start_turn
from claude_log.config import buffer_path
from claude_log.hooks.message_display import run

from .conftest import run_hook


def test_accumulates_delta_across_calls(project_root, monkeypatch):
    path = buffer_path(project_root, "sess1", "prompt1")
    start_turn(path, "do something", None, {})

    run_hook(
        monkeypatch,
        run,
        {
            "session_id": "sess1",
            "cwd": project_root,
            "prompt_id": "prompt1",
            "message_id": "msg-1",
            "index": 0,
            "final": False,
            "delta": "Working on it",
        },
    )
    run_hook(
        monkeypatch,
        run,
        {
            "session_id": "sess1",
            "cwd": project_root,
            "prompt_id": "prompt1",
            "message_id": "msg-1",
            "index": 1,
            "final": True,
            "delta": ", done.",
        },
    )

    with open(path) as buffer_file:
        buffer = json.load(buffer_file)
    assert buffer["assistant_messages"] == ["Working on it, done."]
