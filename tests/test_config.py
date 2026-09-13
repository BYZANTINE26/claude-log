import logging
import os

from claude_log import config

from .conftest import write_config


def test_load_config_defaults_when_no_file(plugin_home):
    assert config.load_config() == config.DEFAULT_CONFIG


def test_load_config_merges_overrides(plugin_home):
    write_config(plugin_home, {"recent_context_window": 25})
    loaded = config.load_config()
    assert loaded["recent_context_window"] == 25
    assert loaded["enabled"] is True  # untouched default preserved


def test_load_config_survives_malformed_json(plugin_home):
    plugin_home.mkdir(parents=True, exist_ok=True)
    (plugin_home / "config.json").write_text("not json")
    assert config.load_config() == config.DEFAULT_CONFIG


def test_path_helpers_are_project_scoped(project_root):
    assert config.log_file_path(project_root, "sess1") == os.path.join(
        project_root, ".claude-log", "logs", "sess1.jsonl"
    )
    assert config.buffer_path(project_root, "sess1", "prompt1") == os.path.join(
        project_root, ".claude-log", ".buffers", "sess1__prompt1.json"
    )
    assert config.state_path(project_root, "sess1") == os.path.join(
        project_root, ".claude-log", ".state", "sess1.json"
    )


def test_get_logger_writes_to_plugin_home(plugin_home):
    logger = config.get_logger()
    logger.info("hello")
    for handler in logger.handlers:
        handler.flush()
    assert (plugin_home / "internal.log").exists()
    assert "hello" in (plugin_home / "internal.log").read_text()


def test_get_logger_reuses_cached_instance(plugin_home):
    assert config.get_logger() is config.get_logger()


def test_get_logger_level_from_config(plugin_home):
    write_config(plugin_home, {"log_level": "debug"})
    assert config.get_logger().level == logging.DEBUG
