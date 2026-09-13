import json
import subprocess

from claude_log.buffer import start_turn
from claude_log.config import buffer_path
from claude_log.git_snapshot import snapshot_git_state
from claude_log.hooks.stop import run
from claude_log.logger import get_recent_entries

from .conftest import run_hook, write_config


def _init_repo(project_root):
    subprocess.run(["git", "init", "-q"], cwd=project_root, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=project_root, check=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=project_root, check=True)
    (open(f"{project_root}/a.txt", "w")).write("one")
    subprocess.run(["git", "add", "a.txt"], cwd=project_root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=project_root, check=True)


def test_logs_one_entry_with_files_touched(project_root, monkeypatch, plugin_home):
    _init_repo(project_root)
    snapshot = snapshot_git_state(project_root)
    start_turn(buffer_path(project_root, "sess1", "prompt1"), "edit a.txt", snapshot["commit"], snapshot["dirty"])

    with open(f"{project_root}/a.txt", "w") as edited_file:
        edited_file.write("changed during the turn")

    # no summarization_endpoint configured (real endpoint success case is
    # covered below) -> exercises the summary_failed marker path
    write_config(plugin_home, {"summarization_endpoint": None})

    run_hook(
        monkeypatch,
        run,
        {"session_id": "sess1", "cwd": project_root, "prompt_id": "prompt1"},
    )

    entries = get_recent_entries(project_root, "sess1", 10)
    assert len(entries) == 1
    assert entries[0]["summary_failed"] is True
    assert entries[0]["refs"]["files"] == ["a.txt"]


def test_logs_real_summary_on_endpoint_success(project_root, monkeypatch, plugin_home):
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.dumps(
                {"choices": [{"message": {"content": json.dumps({"summary": "Edited a.txt."})}}]}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    write_config(
        plugin_home,
        {
            "summarization_endpoint": {
                "url": f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
                "model": "test-model",
            }
        },
    )

    start_turn(buffer_path(project_root, "sess1", "prompt1"), "edit a.txt", None, {})

    run_hook(
        monkeypatch,
        run,
        {"session_id": "sess1", "cwd": project_root, "prompt_id": "prompt1"},
    )
    server.shutdown()

    entries = get_recent_entries(project_root, "sess1", 10)
    assert entries[0]["summary"] == "Edited a.txt."


def test_empty_turn_logs_nothing(project_root, monkeypatch):
    """No prompt and no assistant messages buffered -> nothing to log."""
    run_hook(
        monkeypatch,
        run,
        {"session_id": "sess1", "cwd": project_root, "prompt_id": "never-started"},
    )
    assert get_recent_entries(project_root, "sess1", 10) == []
