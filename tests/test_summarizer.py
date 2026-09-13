import json
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
