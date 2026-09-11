"""Tests for claude_log.summarizer: rule-based fallback and HTTP path."""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from claude_log.summarizer import rule_based_summary, summarize


def test_rule_based_summary_for_edit_only_turn():
    turn = {
        "prompt": "fix the typo",
        "tool_calls": [
            {
                "tool_name": "Edit",
                "result_summary": "ok",
                "tool_input": {"file_path": "README.md"},
            }
        ],
    }
    summary = rule_based_summary(turn)
    assert "README.md" in summary


def test_rule_based_summary_for_tool_only_turn():
    turn = {
        "prompt": None,
        "tool_calls": [
            {"tool_name": "Bash", "result_summary": "ok", "tool_input": {}},
            {"tool_name": "Read", "result_summary": "ok", "tool_input": {}},
        ],
    }
    summary = rule_based_summary(turn)
    assert "Bash" in summary and "Read" in summary


def test_rule_based_summary_for_prompt_only_turn():
    turn = {"prompt": "what does this project do?", "tool_calls": []}
    summary = rule_based_summary(turn)
    assert "what does this project do?" in summary


def test_summarize_uses_rule_based_when_no_endpoint_configured(config):
    turn = {"prompt": "hello", "tool_calls": []}
    assert summarize([], turn, config) == rule_based_summary(turn)


def _start_fake_summarization_server(response_body: dict, delay_seconds: float = 0):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802 - required method name
            import time

            if delay_seconds:
                time.sleep(delay_seconds)
            length = int(self.headers["Content-Length"])
            self.rfile.read(length)
            body = json.dumps(response_body).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):  # silence test output
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def test_summarize_calls_http_endpoint_on_success(config):
    server = _start_fake_summarization_server({"summary": "from the endpoint"})
    try:
        config["summarization_endpoint"] = f"http://127.0.0.1:{server.server_port}"
        result = summarize([], {"prompt": "hi", "tool_calls": []}, config)
        assert result == "from the endpoint"
    finally:
        server.shutdown()


def test_summarize_falls_back_on_timeout(config, monkeypatch):
    from claude_log import summarizer

    def raise_timeout(*args, **kwargs):
        raise TimeoutError("simulated timeout")

    monkeypatch.setattr(summarizer, "call_http_endpoint", raise_timeout)
    config["summarization_endpoint"] = "http://127.0.0.1:1"
    turn = {"prompt": "hello", "tool_calls": []}

    assert summarize([], turn, config) == rule_based_summary(turn)
