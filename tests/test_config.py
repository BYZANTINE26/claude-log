"""Tests for claude_log.config: loading claude_log_config.json."""

import json
import os

from claude_log.config import DEFAULT_CONFIG, load_config


def test_load_config_returns_defaults_when_file_missing(project_root):
    assert load_config(project_root) == DEFAULT_CONFIG


def test_load_config_merges_user_overrides(project_root):
    claude_dir = os.path.join(project_root, ".claude")
    os.makedirs(claude_dir, exist_ok=True)
    config_path = os.path.join(claude_dir, "claude_log_config.json")
    with open(config_path, "w", encoding="utf-8") as config_file:
        json.dump({"verbosity": "rich"}, config_file)

    config = load_config(project_root)
    assert config["verbosity"] == "rich"
    assert config["enabled"] is True  # unspecified keys keep their default


def test_load_config_falls_back_on_malformed_json(project_root):
    claude_dir = os.path.join(project_root, ".claude")
    os.makedirs(claude_dir, exist_ok=True)
    config_path = os.path.join(claude_dir, "claude_log_config.json")
    with open(config_path, "w", encoding="utf-8") as config_file:
        config_file.write("{not valid json")

    assert load_config(project_root) == DEFAULT_CONFIG
