"""Shared fixtures: an isolated ~/.claude-log and project directory so
tests never touch the real machine-level config or a real project."""

import json
import logging

import pytest

from claude_log import config as config_module


@pytest.fixture(autouse=True)
def reset_logger_cache():
    """get_logger() caches its handler per-process, and the underlying
    named logger is a process-wide singleton — both need resetting so
    each test (pointed at its own tmp `HOME`) starts clean."""
    config_module._logger = None
    logging.getLogger("claude_log").handlers.clear()
    yield
    config_module._logger = None
    logging.getLogger("claude_log").handlers.clear()


@pytest.fixture
def plugin_home(tmp_path, monkeypatch):
    """Redirect `~` so `config.plugin_home()` resolves inside tmp_path."""
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setenv("HOME", str(home_dir))
    return home_dir / ".claude-log"


@pytest.fixture
def project_root(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    return str(project_dir)


def write_config(plugin_home, overrides: dict) -> None:
    """Write `~/.claude-log/config.json` with the given overrides."""
    plugin_home.mkdir(parents=True, exist_ok=True)
    with open(plugin_home / "config.json", "w", encoding="utf-8") as config_file:
        json.dump(overrides, config_file)
