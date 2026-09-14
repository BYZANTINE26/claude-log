import json
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from claude_log import summarizer


def _make_server(handler_class):
    server = HTTPServer(("127.0.0.1", 0), handler_class)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


@pytest.fixture
def endpoint_url():
    """Yields (server, url); caller sets the handler class per test."""
    servers = []

    def start(handler_class):
        server = _make_server(handler_class)
        servers.append(server)
        return f"http://127.0.0.1:{server.server_port}/v1/chat/completions"

    yield start
    for server in servers:
        server.shutdown()


def _openai_response(summary_text: str) -> dict:
    return {"choices": [{"message": {"content": json.dumps({"summary": summary_text})}}]}


def test_summarize_success(endpoint_url):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            body = json.dumps(_openai_response("Added a helper function.")).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    config = {
        "summarization_endpoint": {
            "url": endpoint_url(Handler),
            "model": "test-model",
        }
    }
    result = summarizer.summarize([], "add a helper", ["Added it."], config)
    assert result == "Added a helper function."


def test_summarize_no_endpoint_configured_returns_none():
    assert summarizer.summarize([], "prompt", [], {"summarization_endpoint": None}) is None


def test_summarize_timeout_returns_none(endpoint_url):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            import time

            time.sleep(2)
            self.send_response(200)
            self.end_headers()

        def log_message(self, *args):
            pass

    config = {
        "summarization_endpoint": {
            "url": endpoint_url(Handler),
            "model": "test-model",
            "timeout_seconds": 0.2,
        }
    }
    assert summarizer.summarize([], "prompt", [], config) is None


def test_summarize_malformed_response_returns_none(endpoint_url):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b"not json at all")

        def log_message(self, *args):
            pass

    config = {
        "summarization_endpoint": {
            "url": endpoint_url(Handler),
            "model": "test-model",
        }
    }
    assert summarizer.summarize([], "prompt", [], config) is None


def test_summarize_http_error_returns_none(endpoint_url):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.send_response(500)
            self.end_headers()

        def log_message(self, *args):
            pass

    config = {
        "summarization_endpoint": {
            "url": endpoint_url(Handler),
            "model": "test-model",
        }
    }
    assert summarizer.summarize([], "prompt", [], config) is None


def _claude_code_cli_response(summary_text: str) -> str:
    """Shape confirmed live against a real `claude -p ... --output-format
    json --json-schema ...` call (see .planning/findings.md's spike)."""
    return json.dumps({
        "is_error": False,
        "result": json.dumps({"summary": summary_text}),
        "structured_output": {"summary": summary_text},
        "usage": {"output_tokens_details": {"thinking_tokens": 0}},
    })


def test_summarize_claude_code_provider_success(monkeypatch):
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command, 0, stdout=_claude_code_cli_response("Added a helper function."), stderr=""
        )

    monkeypatch.setattr(summarizer.subprocess, "run", fake_run)
    config = {
        "summarization_endpoint": {"provider": "claude-code", "model": "claude-haiku-4-5-20251001"}
    }
    assert summarizer.summarize([], "add a helper", ["Added it."], config) == "Added a helper function."


def test_claude_code_provider_command_disables_hooks_tools_and_thinking(monkeypatch):
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["env"] = kwargs["env"]
        return subprocess.CompletedProcess(command, 0, stdout=_claude_code_cli_response("ok"), stderr="")

    monkeypatch.setattr(summarizer.subprocess, "run", fake_run)
    endpoint_config = {"provider": "claude-code", "model": "claude-haiku-4-5-20251001"}
    summarizer.call_claude_code_provider(endpoint_config, [], "prompt", [])

    command = captured["command"]
    assert "--safe-mode" in command
    assert command[command.index("--tools") + 1] == ""  # disables built-in tools too
    assert captured["env"]["MAX_THINKING_TOKENS"] == "0"


def test_claude_code_provider_warns_when_model_is_fable(monkeypatch):
    """`internal.log`'s logger has `propagate = False` (by design, see
    config.py), so it's checked directly rather than via caplog."""
    warnings = []

    class FakeLogger:
        def warning(self, message, *args):
            warnings.append(message % args)

        def debug(self, *args, **kwargs):
            pass

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout=_claude_code_cli_response("ok"), stderr="")

    monkeypatch.setattr(summarizer.subprocess, "run", fake_run)
    monkeypatch.setattr(summarizer, "get_logger", lambda: FakeLogger())
    endpoint_config = {"provider": "claude-code", "model": "claude-fable-5-1"}
    summarizer.call_claude_code_provider(endpoint_config, [], "prompt", [])
    assert any("Fable" in warning for warning in warnings)


def test_summarize_claude_code_provider_subprocess_error_returns_none(monkeypatch):
    def fake_run(command, **kwargs):
        raise subprocess.CalledProcessError(1, command, stderr="boom")

    monkeypatch.setattr(summarizer.subprocess, "run", fake_run)
    config = {
        "summarization_endpoint": {"provider": "claude-code", "model": "claude-haiku-4-5-20251001"}
    }
    assert summarizer.summarize([], "prompt", [], config) is None


def test_summarize_claude_code_provider_timeout_returns_none(monkeypatch):
    def fake_run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, kwargs.get("timeout"))

    monkeypatch.setattr(summarizer.subprocess, "run", fake_run)
    config = {
        "summarization_endpoint": {
            "provider": "claude-code", "model": "claude-haiku-4-5-20251001", "timeout_seconds": 1
        }
    }
    assert summarizer.summarize([], "prompt", [], config) is None


def test_build_user_content_includes_recent_and_current_turn():
    content = summarizer._build_user_content(
        [{"summary": "did X"}, {"summary": "did Y"}], "do Z", ["I did Z."]
    )
    assert "1. did X" in content
    assert "2. did Y" in content
    assert "User: do Z" in content
    assert "Assistant: I did Z." in content


def test_build_user_content_with_no_recent_entries():
    content = summarizer._build_user_content([], "do Z", ["Done."])
    assert "(none)" in content
