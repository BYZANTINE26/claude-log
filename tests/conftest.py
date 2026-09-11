"""Shared pytest fixtures: a temp project directory with default config."""

import io
import json
import os

import pytest

from claude_log.config import DEFAULT_CONFIG

FIXTURES_DIRECTORY = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def project_root(tmp_path):
    """A temp directory standing in for a Claude Code project root."""
    return str(tmp_path)


@pytest.fixture
def config():
    """A fresh copy of the default config for tests to override."""
    return dict(DEFAULT_CONFIG)


def load_fixture(fixture_name: str, project_root: str) -> dict:
    """Load a canned hook-input fixture and stamp it with a real cwd."""
    fixture_path = os.path.join(FIXTURES_DIRECTORY, fixture_name)
    with open(fixture_path, "r", encoding="utf-8") as fixture_file:
        hook_input = json.load(fixture_file)
    hook_input["cwd"] = project_root
    return hook_input


def run_hook(monkeypatch, run_function, hook_input: dict) -> None:
    """Feed hook_input on stdin and run a hook's guarded entry point."""
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(hook_input)))
    monkeypatch.setattr("sys.exit", lambda *_args: None)
    run_function()
