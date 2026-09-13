"""claude-log's plugin environment: settings, paths, and its own logger.

Config and the internal operational log are machine-scoped
(`~/.claude-log/`), separate from any single project's data — see
docs/adr/0002. Session logs, buffers, and state are project-scoped and
resolved relative to `project_root` instead.
"""

import json
import logging
import logging.handlers
import os

DEFAULT_CONFIG = {
    "enabled": True,
    "recent_context_window": 10,
    "summarization_endpoint": None,  # dict: url/model/api_key/extra_params
    "log_level": "info",
}

_LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}

_logger = None  # module-level cache so repeated calls reuse one handler


def plugin_home() -> str:
    """`~/.claude-log` — claude-log's own machine-scoped directory."""
    return os.path.expanduser("~/.claude-log")


def load_config() -> dict:
    """Read `~/.claude-log/config.json`, falling back to defaults.

    Missing file, unreadable file, or invalid JSON all degrade to
    DEFAULT_CONFIG rather than raising — a broken config must never
    block the user's Claude Code session.
    """
    config = dict(DEFAULT_CONFIG)
    config_path = os.path.join(plugin_home(), "config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            user_config = json.load(config_file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return config
    if isinstance(user_config, dict):
        config.update(user_config)
    return config


def project_log_dir(project_root: str) -> str:
    """`<project_root>/.claude-log` — this project's claude-log data."""
    return os.path.join(project_root, ".claude-log")


def log_file_path(project_root: str, session_id: str) -> str:
    return os.path.join(project_log_dir(project_root), "logs", f"{session_id}.jsonl")


def buffer_path(project_root: str, session_id: str, prompt_id: str) -> str:
    """Flat file, `session_id` kept in the name so a session's leftover
    buffers can be found by prefix (see docs/adr/0006)."""
    return os.path.join(
        project_log_dir(project_root), ".buffers", f"{session_id}__{prompt_id}.json"
    )


def state_path(project_root: str, session_id: str) -> str:
    return os.path.join(project_log_dir(project_root), ".state", f"{session_id}.json")


def get_logger() -> logging.Logger:
    """claude-log's own operational logger — rotating file, no stderr.

    Level comes from config (`debug`/`info`/`warning`/`error`); the
    handler is created once per process and reused on subsequent calls.
    """
    global _logger
    if _logger is not None:
        return _logger

    home = plugin_home()
    os.makedirs(home, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        os.path.join(home, "internal.log"),
        maxBytes=1_000_000,
        backupCount=3,
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )

    logger = logging.getLogger("claude_log")
    logger.setLevel(_LOG_LEVELS.get(load_config()["log_level"], logging.INFO))
    logger.addHandler(handler)
    logger.propagate = False  # never let this reach stderr/root handlers

    _logger = logger
    return logger
