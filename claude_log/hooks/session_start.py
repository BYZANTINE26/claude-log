"""SessionStart hook: create/resume the session log, reset the turn buffer.

A SessionStart always means no turn is currently in progress, so the
buffer is reset unconditionally — this is the one point in the lifecycle
guaranteed not to be mid-turn.
"""

import sys

from claude_log import config as config_module
from claude_log import logger
from claude_log.buffer import reset_buffer
from claude_log.hooks._hook_io import emit_ok, read_hook_input, resolve_project_root
from claude_log.paths import turn_buffer_path


def main() -> None:
    hook_input = read_hook_input()
    project_root = resolve_project_root(hook_input)
    config = config_module.load_config(project_root)

    if not config.get("enabled", True):
        emit_ok()
        return

    session_id = hook_input.get("session_id", "unknown-session")
    logger.initialize_or_resume(project_root, session_id, config)
    reset_buffer(turn_buffer_path(project_root, session_id, config))
    emit_ok()


def run() -> None:
    """Guarded entry point: never let a bug block the user's session."""
    try:
        main()
    except Exception as error:  # noqa: BLE001 - never block the user's session
        print(f"claude-log SessionStart failed: {error}", file=sys.stderr)
        emit_ok()


if __name__ == "__main__":
    run()
