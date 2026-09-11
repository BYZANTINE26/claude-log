"""Load claude-log configuration.

Config lives in its own file (.claude/claude_log_config.json), not in
Claude Code's .claude/settings.json — that file's schema rejects unknown
top-level keys, so a "logging" key there fails settings validation.
"""

import json
import os

DEFAULT_CONFIG = {
    "enabled": True,
    "verbosity": "slim",
    "recent_context_window": 10,
    "summarization_endpoint": None,
    "log_directory": ".claude/logs",
}

CONFIG_FILE_NAME = "claude_log_config.json"


def load_config(project_root: str) -> dict:
    """Merge .claude/claude_log_config.json over the defaults.

    Missing file, or malformed JSON, both fall back silently to
    DEFAULT_CONFIG — a misconfigured file must never crash a hook.
    """
    config_path = os.path.join(project_root, ".claude", CONFIG_FILE_NAME)
    config = dict(DEFAULT_CONFIG)

    try:
        with open(config_path, "r", encoding="utf-8") as config_file:
            user_config = json.load(config_file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return config

    if isinstance(user_config, dict):
        config.update(user_config)

    return config
