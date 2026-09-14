from claude_log import logger
from claude_log.hooks.session_start import run

from .conftest import run_hook


def test_clear_marks_context_reset(project_root, monkeypatch):
    for index in range(3):
        path = logger.initialize_or_resume(project_root, "sess1")
        logger.append_entry(path, logger.build_entry(f"t{index}", "ts", "s", {}))

    run_hook(
        monkeypatch,
        run,
        {"session_id": "sess1", "cwd": project_root, "source": "clear"},
    )

    assert logger.get_recent_entries(project_root, "sess1", 10) == []


def test_resume_does_not_mark_reset(project_root, monkeypatch):
    for index in range(3):
        path = logger.initialize_or_resume(project_root, "sess1")
        logger.append_entry(path, logger.build_entry(f"t{index}", "ts", "s", {}))

    run_hook(
        monkeypatch,
        run,
        {"session_id": "sess1", "cwd": project_root, "source": "resume"},
    )

    assert len(logger.get_recent_entries(project_root, "sess1", 10)) == 3


def test_disabled_config_is_a_no_op(project_root, monkeypatch, plugin_home):
    from .conftest import write_config

    write_config(plugin_home, {"enabled": False})
    run_hook(
        monkeypatch,
        run,
        {"session_id": "sess1", "cwd": project_root, "source": "clear"},
    )
    # no state file written, no crash
    assert len(logger.get_recent_entries(project_root, "sess1", 10)) == 0
